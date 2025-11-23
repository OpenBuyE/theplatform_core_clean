"""
participant_repository.py
Repositorio seguro para gestión de participantes.
"""

from datetime import datetime
from typing import Dict, List

from .supabase_client import supabase
from .audit_repository import log_event

PARTICIPANT_TABLE = "ca_session_participants"


class ParticipantRepository:

    # ---------------------------------------------------------
    # Obtener participantes de una sesión
    # ---------------------------------------------------------
    def get_participants_by_session(self, session_id: str) -> List[Dict]:
        response = (
            supabase.table(PARTICIPANT_TABLE)
            .select("*")
            .eq("session_id", session_id)
            .order("created_at")
            .execute()
        )
        return response.data or []

    # ---------------------------------------------------------
    # Añadir participante de prueba (ONLY TEST)
    # ---------------------------------------------------------
    def add_test_participant(self, session: Dict):
        """
        Recibe el dict completo de la sesión.
        Con esto evitamos errores por índices incorrectos.
        """

        session_id = session["id"]
        organization_id = session["organization_id"]
        index = (session.get("pax_registered") or 0) + 1

        now = datetime.utcnow().isoformat()

        payload = {
            "session_id": session_id,
            "user_id": f"TEST-USER-{index}",
            "organization_id": organization_id,
            "amount": 0,
            "price": 0,
            "quantity": 1,
            "is_awarded": False,
            "created_at": now,
        }

        response = supabase.table(PARTICIPANT_TABLE).insert(payload).execute()

        if not response.data:
            log_event(
                action="test_participant_insert_error",
                session_id=session_id,
                metadata={"payload": payload}
            )
            return None

        inserted = response.data[0]

        log_event(
            action="test_participant_added",
            session_id=session_id,
            user_id=inserted["user_id"]
        )

        return inserted


# Instancia global
participant_repository = ParticipantRepository()
