"""
participant_repository.py
Versión BLINDADA (PASO 4) sin imports circulares.

Responsabilidades:
- Insertar participantes en la sesión
- Verificar que la sesión es válida (activa, no expirada)
- Blindar aforo: NUNCA superar capacity
- Disparar adjudicación determinista al completar aforo
- Consultar participantes y adjudicatarios
"""

from datetime import datetime
from typing import List, Dict, Optional

from .supabase_client import supabase
from .audit_repository import log_event
from .session_repository import session_repository


PARTICIPANT_TABLE = "ca_session_participants"  # <-- nombre tabla nuevo


class ParticipantRepository:
    # -----------------------------------------------------
    # Obtener todos los participantes de una sesión
    # -----------------------------------------------------
    def get_participants_by_session(self, session_id: str) -> List[Dict]:
        response = (
            supabase
            .table(PARTICIPANT_TABLE)
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", asc=True)
            .execute()
        )
        return response.data or []

    # -----------------------------------------------------
    # ¿Existe ya un adjudicatario?
    # -----------------------------------------------------
    def exists_awarded_participant(self, session_id: str) -> bool:
        response = (
            supabase
            .table(PARTICIPANT_TABLE)
            .select("id")
            .eq("session_id", session_id)
            .eq("is_awarded", True)
            .execute()
        )
        return len(response.data or []) > 0

    # -----------------------------------------------------
    # INSERTAR PARTICIPANTE (BLINDADO)
    # -----------------------------------------------------
    def add_participant(
        self,
        session_id: str,
        user_id: str,
        organization_id: str,
        amount: float,
        price: float,
        quantity: int,
    ) -> Optional[Dict]:
        """
        Inserta un participante respetando SIEMPRE:

        - La sesión debe existir.
        - Debe estar en estado 'active'.
        - No puede estar expirada (expires_at < ahora).
        - NUNCA se puede superar capacity (aforo).
        - Al llegar exactamente a capacity ⇒ se dispara adjudicación.

        Si alguna condición falla, devuelve None y registra en ca_audit_logs.
        """

        now_iso = datetime.utcnow().isoformat()

        # 0) Cargar sesión
        session = session_repository.get_session_by_id(session_id)
        if not session:
            log_event(
                action="participant_rejected_session_not_found",
                session_id=session_id,
                user_id=user_id,
                metadata={}
            )
            return None

        # Solo sesiones activas
        if session.get("status") != "active":
            log_event(
                action="participant_rejected_session_not_active",
                session_id=session_id,
                user_id=user_id,
                metadata={"status": session.get("status")}
            )
            return None

        # No expirada
        expires_at = session.get("expires_at")
        if expires_at and expires_at < now_iso:
            log_event(
                action="participant_rejected_session_expired",
                session_id=session_id,
                user_id=user_id,
                metadata={"expires_at": expires_at}
            )
            return None

        # Blindaje de aforo
        capacity = session.get("capacity", 0)
        pax_registered = session.get("pax_registered", 0)

        if capacity <= 0:
            log_event(
                action="participant_rejected_invalid_capacity",
                session_id=session_id,
                user_id=user_id,
                metadata={"capacity": capacity}
            )
            return None

        # 🚫 NUNCA superar aforo
        if pax_registered >= capacity:
            log_event(
                action="participant_rejected_capacity_full",
                session_id=session_id,
                user_id=user_id,
                metadata={
                    "pax_registered": pax_registered,
                    "capacity": capacity
                }
            )
            return None

        # 1) Insertar participante
        insert_response = (
            supabase
            .table(PARTICIPANT_TABLE)
            .insert({
                "session_id": session_id,
                "user_id": user_id,
                "organization_id": organization_id,
                "amount": amount,
                "price": price,
                "quantity": quantity,
                "is_awarded": False,
                "created_at": now_iso
            })
            .execute()
        )

        if not insert_response.data:
            log_event(
                action="participant_insert_error",
                session_id=session_id,
                user_id=user_id,
                metadata={}
            )
            return None

        participant = insert_response.data[0]

        log_event(
            action="participant_added",
            session_id=session_id,
            user_id=user_id,
            metadata={"participant_id": participant["id"]}
        )

        # 2) Incrementar pax_registered (en repositorio de sesiones)
        session_repository.increment_pax_registered(session_id)

        # 3) Recargar sesión para saber el nuevo aforo registrado
        updated_session = session_repository.get_session_by_id(session_id)
        if not updated_session:
            log_event(
                action="participant_added_session_not_found_after_insert",
                session_id=session_id,
                user_id=user_id,
                metadata={}
            )
            return participant

        new_pax_registered = updated_session.get("pax_registered", pax_registered + 1)

        # 4) Si se ha completado EXACTAMENTE el aforo → adjudicar
        if (
            new_pax_registered == capacity
            and updated_session.get("status") == "active"
            and (not updated_session.get("expires_at") or updated_session["expires_at"] > now_iso)
        ):
            # Importación diferida para evitar import circular
            try:
                from .adjudicator_engine import adjudicator_engine
                adjudicator_engine.adjudicate_session(session_id)
            except Exception as e:
                log_event(
                    action="participant_adjudication_trigger_failed",
                    session_id=session_id,
                    user_id=user_id,
                    metadata={"error": str(e)}
                )

        return participant

    # -----------------------------------------------------
    # Marcar participante adjudicatario
    # -----------------------------------------------------
    def mark_as_awarded(self, participant_id: str, awarded_at: str) -> None:
        (
            supabase
            .table(PARTICIPANT_TABLE)
            .update({
                "is_awarded": True,
                "awarded_at": awarded_at
            })
            .eq("id", participant_id)
            .execute()
        )

        log_event(
            action="participant_marked_awarded",
            session_id=None,
            user_id=None,
            metadata={"participant_id": participant_id, "awarded_at": awarded_at}
        )

    # -----------------------------------------------------
    # Obtener adjudicatario (si existe)
    # -----------------------------------------------------
    def get_awarded_participant(self, session_id: str) -> Optional[Dict]:
        response = (
            supabase
            .table(PARTICIPANT_TABLE)
            .select("*")
            .eq("session_id", session_id)
            .eq("is_awarded", True)
            .maybe_single()
            .execute()
        )
        return response.data


# Instancia global
participant_repository = ParticipantRepository()
