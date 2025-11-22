"""
participant_repository.py
Gestión de participantes de sesiones Compra Abierta.
"""

from datetime import datetime
from typing import List, Dict, Optional

from .supabase_client import supabase
from .audit_repository import log_event

PARTICIPANT_TABLE = "ca_session_participants"


class ParticipantRepository:

    # ---------------------------------------------------------
    # Obtener participantes por sesión
    # ---------------------------------------------------------
    def get_participants_by_session(self, session_id: str) -> List[Dict]:
        response = (
            supabase
            .table(PARTICIPANT_TABLE)
            .select("*")
            .eq("session_id", session_id)
            .order("created_at")      # SIN asc=True (PostgREST 11 no lo acepta)
            .execute()
        )
        return response.data or []

    # ---------------------------------------------------------
    # Insertar participante de TEST
    # ---------------------------------------------------------
    def add_test_participant(self, session: Dict) -> Optional[Dict]:

        now = datetime.utcnow().isoformat()

        payload = {
            "session_id": session["id"],
            "user_id": f"TEST-USER-{session['pax_registered']+1}",
            "organization_id": session["organization_id"],
            "amount": 0,
            "quantity": 0,
            "price": 1,
            "is_awarded": False,
            "created_at": now
        }

        response = (
            supabase
            .table(PARTICIPANT_TABLE)
            .insert(payload)
            .execute()
        )

        if not response.data:
            log_event(
                action="participant_insert_error",
                session_id=session["id"],
                metadata={"payload": payload}
            )
            return None

        participant = response.data[0]

        log_event(
            action="participant_added_test",
            session_id=session["id"],
            user_id=participant["user_id"],
            metadata={"participant_id": participant["id"]}
        )

        return participant

    # ---------------------------------------------------------
    # Marcar adjudicatario
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
            metadata={"participant_id": participant_id}
        )


# ---------------------------------------------------------
# Instancia global (NECESARIA para que lo importe el panel)
# ---------------------------------------------------------
participant_repository = ParticipantRepository()
