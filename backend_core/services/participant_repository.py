"""
participant_repository.py
Gestión de participantes de sesiones Compra Abierta.

Responsabilidades:
- Insertar participantes en la sesión
- Verificar si ya existe un adjudicatario en la sesión
- Obtener lista de participantes
- Disparar adjudicación cuando se completa aforo
"""

from datetime import datetime
from typing import List, Dict, Optional

from .supabase_client import supabase
from .audit_repository import log_event
from .session_repository import session_repository
from .adjudicator_engine import adjudicator_engine


PARTICIPANT_TABLE = "session_participants"


class ParticipantRepository:

    # ---------------------------------------------------------
    #  Obtener participantes de una sesión
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    #  Comprobar si ya existe un adjudicatario en la sesión
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
    #  Insertar participante en sesión
    #  (Y disparar adjudicación si aforo se completa)
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

        now = datetime.utcnow().isoformat()

        # 1. Insertar participante
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
                "created_at": now
            })
            .execute()
        )

        if not insert_response.data:
            log_event(
                action="participant_insert_error",
                session_id=session_id,
                user_id=user_id
            )
            return None

        participant = insert_response.data[0]

        log_event(
            action="participant_added",
            session_id=session_id,
            user_id=user_id,
            metadata={"participant_id": participant["id"]}
        )

        # 2. Incrementar pax_registered
        session_repository.increment_pax_registered(session_id)

        # 3. Recargar sesión
        session = session_repository.get_session_by_id(session_id)
        if not session:
            log_event(
                action="participant_added_session_not_found",
                session_id=session_id
            )
            return participant

        # 4. Si aforo completo → adjudicar
        if (
            session["pax_registered"] == session["capacity"]
            and session["expires_at"] > datetime.utcnow().isoformat()
        ):
            adjudicator_engine.adjudicate_session(session_id)

        return participant

    # ---------------------------------------------------------
    #  Marcar participante como adjudicatario
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
            session_id=None,
            metadata={"participant_id": participant_id}
        )


# Instancia global exportable
participant_repository = ParticipantRepository()
