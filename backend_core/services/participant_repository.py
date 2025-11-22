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
            .order("created_at", desc=False)
            .execute()
        )
        return response.data or []

    # ---------------------------------------------------------
    #  Insertar participante con bloqueo de aforo
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

        session = session_repository.get_session_by_id(session_id)
        if not session:
            log_event(
                action="participant_insert_session_not_found",
                session_id=session_id,
                user_id=user_id,
            )
            return None

        pax = session.get("pax_registered", 0)
        cap = session.get("capacity", 0)

        # 🔥 BLOQUEO: aforo completo → NO insertar
        if pax >= cap:
            log_event(
                action="participant_insert_capacity_full",
                session_id=session_id,
                user_id=user_id,
                metadata={"pax_registered": pax, "capacity": cap},
            )
            return None

        now = datetime.utcnow().isoformat()

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

        # Incrementar aforo real
        session_repository.increment_pax_registered(session_id)

        log_event(
            action="participant_added",
            session_id=session_id,
            user_id=user_id,
            metadata={"participant_id": participant["id"]}
        )

        return participant


participant_repository = ParticipantRepository()
