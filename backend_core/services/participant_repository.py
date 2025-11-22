"""
participant_repository.py
Gestión de participantes de sesiones Compra Abierta.

Responsabilidades:
- Insertar participantes en la sesión (flujo real)
- Verificar si ya existe un adjudicatario en la sesión
- Obtener lista de participantes
- Marcar adjudicatario
- Lógica de disparo de adjudicación al completar aforo

Blindaje PASO 4.1:
- NO permite insertar participantes si:
  - la sesión no existe
  - la sesión no está active
  - la sesión ha expirado
  - la sesión ya ha completado aforo (pax_registered >= capacity)
- Solo el backend controla pax_registered (incremento interno controlado).
"""

from datetime import datetime
from typing import List, Dict, Optional

from .supabase_client import supabase
from .audit_repository import log_event
from .session_repository import session_repository


PARTICIPANT_TABLE = "ca_session_participants"  # usamos la tabla nueva


class ParticipantRepository:
    # ---------------------------------------------------------
    #  Obtener todos los participantes de una sesión
    # ---------------------------------------------------------
    def get_participants_by_session(self, session_id: str) -> List[Dict]:
        response = (
            supabase
            .table(PARTICIPANT_TABLE)
            .select("*")
            .eq("session_id", session_id)
            .order("created_at")  # ascendente por defecto
            .execute()
        )
        return response.data or []

    # ---------------------------------------------------------
    #  ¿Existe ya un adjudicatario?
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    #  Insertar participante (flujo REAL)
    #  Blindado: valida estado de sesión y aforo ANTES de insertar
    # ---------------------------------------------------------
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
        Flujo real (no test) de inserción de participante.

        REGLAS:
        - La sesión debe existir.
        - Debe estar 'active'.
        - No puede estar expirada.
        - pax_registered < capacity (aforo no completo).
        """

        # 0) Cargar sesión
        session = session_repository.get_session_by_id(session_id)
        if not session:
            log_event(
                action="participant_add_blocked_session_not_found",
                session_id=session_id,
                user_id=user_id,
            )
            return None

        status = session.get("status")
        capacity = session.get("capacity", 0)
        pax_registered = session.get("pax_registered", 0)
        expires_at = session.get("expires_at")

        now_iso = datetime.utcnow().isoformat()

        # 1) Debe estar active
        if status != "active":
            log_event(
                action="participant_add_blocked_session_not_active",
                session_id=session_id,
                user_id=user_id,
                metadata={"status": status}
            )
            return None

        # 2) No expirado
        if expires_at and expires_at < now_iso:
            log_event(
                action="participant_add_blocked_session_expired",
                session_id=session_id,
                user_id=user_id,
                metadata={"expires_at": expires_at}
            )
            return None

        # 3) Aforo no completo
        if pax_registered >= capacity:
            log_event(
                action="participant_add_blocked_capacity_reached",
                session_id=session_id,
                user_id=user_id,
                metadata={
                    "pax_registered": pax_registered,
                    "capacity": capacity,
                }
            )
            return None

        # 4) Insertar participante
        now = now_iso

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
                "created_at": now,
            })
            .execute()
        )

        if not insert_response.data:
            log_event(
                action="participant_insert_error",
                session_id=session_id,
                user_id=user_id,
            )
            return None

        participant = insert_response.data[0]

        log_event(
            action="participant_added",
            session_id=session_id,
            user_id=user_id,
            metadata={"participant_id": participant["id"]}
        )

        # 5) Incrementar pax_registered (LADO BACKEND, controlado)
        session_repository.increment_pax_registered(session_id)

        # 6) Recargar sesión tras incremento
        session = session_repository.get_session_by_id(session_id)
        if not session:
            log_event(
                action="participant_added_session_not_found_after_increment",
                session_id=session_id
            )
            return participant

        pax_registered = session.get("pax_registered", 0)
        capacity = session.get("capacity", 0)
        expires_at = session.get("expires_at")

        # 7) Si aforo completo y no caducado → adjudicar
        if (
            pax_registered == capacity
            and (not expires_at or expires_at > datetime.utcnow().isoformat())
        ):
            # Import diferido para evitar import circular
            from .adjudicator_engine import adjudicator_engine
            adjudicator_engine.adjudicate_session(session_id)

        return participant

    # ---------------------------------------------------------
    #  Marcar participante adjudicatario
    # ---------------------------------------------------------
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
            metadata={
                "participant_id": participant_id,
                "awarded_at": awarded_at,
            }
        )

    # ---------------------------------------------------------
    #  Obtener adjudicatario (si existe)
    # ---------------------------------------------------------
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
