"""
participant_repository.py
Gestión de participantes de sesiones Compra Abierta.
"""

from datetime import datetime
from typing import List, Dict, Optional
from .supabase_client import supabase
from .audit_repository import log_event
from .session_repository import session_repository

PARTICIPANT_TABLE = "ca_session_participants"


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
            .order("created_at")
            .execute()
        )
        return response.data or []

    # ---------------------------------------------------------
    #  Comprobar si ya existe un adjudicatario
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
    #  Añadir participante Test desde el panel
    # ---------------------------------------------------------
    def add_test_participant(self, session_id: str) -> Optional[Dict]:

        # 1) Cargar sesión real para obtener organization_id
        session = session_repository.get_session_by_id(session_id)
        if not session:
            log_event(
                action="test_participant_error_session_not_found",
                session_id=session_id
            )
            return None

        org_id = session["organization_id"]
        user_id = "TEST-USER"
        now = datetime.utcnow().isoformat()

        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "organization_id": org_id,
            "amount": 0,
            "price": 0,
            "quantity": 1,
            "is_awarded": False,
            "created_at": now
        }

        # 2) Insertar participante Test
        response = (
            supabase
            .table(PARTICIPANT_TABLE)
            .insert(payload)
            .execute()
        )

        if not response.data:
            log_event(
                action="test_participant_insert_error",
                session_id=session_id,
                metadata=payload
            )
            return None

        participant = response.data[0]

        # 3) Subir pax_registered
        session_repository.increment_pax_registered(session_id)

        log_event(
            action="test_participant_added",
            session_id=session_id,
            user_id=user_id,
            metadata={"participant_id": participant["id"]}
        )

        return participant


# Instancia global
participant_repository = ParticipantRepository()
