"""
participant_repository.py
Versión estable sin imports circulares.

Tabla base:
- public.ca_session_participants

Campos clave:
- id, session_id, user_id, organization_id
- amount, price, quantity
- is_awarded, awarded_at, created_at
"""

from datetime import datetime
from typing import List, Dict, Optional

from .supabase_client import supabase
from .audit_repository import log_event
from .session_repository import session_repository


PARTICIPANT_TABLE = "ca_session_participants"


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
            .order("created_at")  # asc por defecto
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
    # Insertar participante + trigger de adjudicación
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

        now = datetime.utcnow().isoformat()

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
            metadata={"participant_id": participant["id"]},
        )

        # 2) Incrementar pax_registered
        session_repository.increment_pax_registered(session_id)

        # 3) Recargar sesión
        session = session_repository.get_session_by_id(session_id)
        if not session:
            log_event(
                action="participant_added_session_not_found",
                session_id=session_id,
            )
            return participant

        # 4) Si aforo completo → adjudicar
        if (
            session["pax_registered"] == session["capacity"]
            and session["expires_at"] > datetime.utcnow().isoformat()
        ):
            # Importación diferida evita import circular
            from .adjudicator_engine import adjudicator_engine

            adjudicator_engine.adjudicate_session(session_id)

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
                "awarded_at": awarded_at,
            })
            .eq("id", participant_id)
            .execute()
        )

        log_event(
            action="participant_marked_awarded",
            session_id=None,
            metadata={
                "participant_id": participant_id,
                "awarded_at": awarded_at,
            },
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
