"""
participant_repository.py
Gestión y escritura de participantes en sesiones Compra Abierta.
Compatible con esquema ca_session_participants.
"""

from datetime import datetime
from typing import List, Dict, Optional

from .supabase_client import supabase
from .audit_repository import log_event
from .session_repository import session_repository


PARTICIPANT_TABLE = "ca_session_participants"


class ParticipantRepository:

    # ---------------------------------------------------------
    #  Obtener participantes
    # ---------------------------------------------------------
    def get_participants_by_session(self, session_id: str) -> List[Dict]:
        response = (
            supabase
            .table(PARTICIPANT_TABLE)
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .execute()
        )
        return response.data or []

    # ---------------------------------------------------------
    #  Insertar participante REAL (API / Smart Contract)
    # ---------------------------------------------------------
    def add_participant(
        self,
        session_id: str,
        user_id: str,
        amount: float = 0.0,
        quantity: int = 1,
        price: float = 0.0
    ) -> Optional[Dict]:

        now = datetime.utcnow().isoformat()

        # Obtener organization_id desde la sesión
        session = session_repository.get_session_by_id(session_id)
        if not session:
            return None

        organization_id = session["organization_id"]

        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "organization_id": organization_id,
            "amount": amount,
            "quantity": quantity,
            "price": price,
            "is_awarded": False,
            "created_at": now
        }

        response = supabase.table(PARTICIPANT_TABLE).insert(payload).execute()

        if not response.data:
            log_event(
                action="participant_insert_error",
                session_id=session_id,
                user_id=user_id
            )
            return None

        # incrementar pax_registered
        session_repository.increment_pax_registered(session_id)

        return response.data[0]

    # ---------------------------------------------------------
    #  Insertar participante TEST (botón Active Sessions)
    # ---------------------------------------------------------
    def add_test_participant(self, session_id: str) -> Optional[Dict]:

        now = datetime.utcnow().isoformat()

        # 1) Recuperar sesión para obtener organization_id
        session = session_repository.get_session_by_id(session_id)
        if not session:
            return None

        organization_id = session["organization_id"]

        # TEST user id
        test_user = f"TEST-{now[:19]}"

        payload = {
            "session_id": session_id,
            "user_id": test_user,
            "organization_id": organization_id,
            "amount": 0,
            "price": 0,
            "quantity": 1,
            "is_awarded": False,
            "created_at": now
        }

        response = supabase.table(PARTICIPANT_TABLE).insert(payload).execute()

        if not response.data:
            log_event(
                action="test_participant_insert_error",
                session_id=session_id,
                metadata={"user": test_user}
            )
            return None

        # actualizar pax_registered en sesiones
        session_repository.increment_pax_registered(session_id)

        log_event(
            action="test_participant_added",
            session_id=session_id,
            metadata={"test_user": test_user}
        )

        return response.data[0]


# Instancia global
participant_repository = ParticipantRepository()
