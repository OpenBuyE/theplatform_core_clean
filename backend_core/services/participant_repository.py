"""
participant_repository.py
Gestión de participantes en sesiones Compra Abierta.
Compatibilidad con tabla: ca_session_participants
"""

from datetime import datetime
from typing import List, Dict, Optional

from .supabase_client import supabase
from .audit_repository import log_event


PARTICIPANT_TABLE = "ca_session_participants"


class ParticipantRepository:

    # ---------------------------------------------------------
    #  Obtener participantes por sesión
    # ---------------------------------------------------------
    def get_participants_by_session(self, session_id: str) -> List[Dict]:
        response = (
            supabase.table(PARTICIPANT_TABLE)
            .select("*")
            .eq("session_id", session_id)
            .order("created_at")       # PostgREST usa ORDER BY creado_at ASC por defecto
            .execute()
        )
        return response.data or []

    # ---------------------------------------------------------
    #  Contar participantes
    # ---------------------------------------------------------
    def count_participants(self, session_id: str) -> int:
        response = (
            supabase.table(PARTICIPANT_TABLE)
            .select("id", count="exact")
            .eq("session_id", session_id)
            .execute()
        )
        return response.count or 0

    # ---------------------------------------------------------
    #  Insertar participante REAL (cuando ya exista wallet)
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

        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "organization_id": organization_id,
            "amount": amount,
            "price": price,
            "quantity": quantity,
            "is_awarded": False,
            "created_at": now
        }

        response = supabase.table(PARTICIPANT_TABLE).insert(payload).execute()

        if not response.data:
            log_event("participant_insert_error", session_id=session_id, metadata=payload)
            return None

        participant = response.data[0]
        log_event("participant_added", session_id=session_id, user_id=user_id)

        return participant

    # ---------------------------------------------------------
    #  Añadir participante de prueba desde el panel
    # ---------------------------------------------------------
    def add_test_participant(self, session_id: str) -> Optional[Dict]:
        """
        Se usa EXCLUSIVAMENTE en el panel operativo para pruebas manuales.
        NO EXISTIRÁ en producción.
        """

        now = datetime.utcnow().isoformat()

        payload = {
            "session_id": session_id,
            "user_id": "TEST-USER",
            "organization_id": None,
            "amount": 0,
            "price": 0,
            "quantity": 1,
            "is_awarded": False,
            "created_at": now
        }

        response = supabase.table(PARTICIPANT_TABLE).insert(payload).execute()

        if not response.data:
            log_event(
                "test_participant_insert_error",
                session_id=session_id,
                metadata=payload,
            )
            return None

        participant = response.data[0]

        log_event(
            "test_participant_added",
            session_id=session_id,
            metadata={"participant_id": participant["id"]},
        )

        return participant


# Instancia global requerida por TODAS las vistas
participant_repository = ParticipantRepository()
