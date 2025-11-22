"""
participant_repository.py
Gestión de participantes para sesiones Compra Abierta.
Adaptado a tablas nuevas: ca_session_participants
"""

from datetime import datetime
from typing import List, Dict, Optional

from .supabase_client import supabase
from .audit_repository import log_event
from .session_repository import session_repository

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
            .order("created_at")
            .execute()
        )
        return response.data or []

    # ---------------------------------------------------------
    #  Comprobar si ya existe adjudicatario
    # ---------------------------------------------------------
    def exists_awarded_participant(self, session_id: str) -> bool:
        response = (
            supabase.table(PARTICIPANT_TABLE)
            .select("id")
            .eq("session_id", session_id)
            .eq("is_awarded", True)
            .execute()
        )
        return len(response.data or []) > 0

    # ---------------------------------------------------------
    #  Añadir participante REAL (futuro: usuario auténtico)
    # ---------------------------------------------------------
    def add_participant(
        self,
        session_id: str,
        user_id: str,
        organization_id: str,
        amount: float,
        quantity: int,
        price: float,
    ) -> Optional[Dict]:

        now = datetime.utcnow().isoformat()

        insert_response = (
            supabase.table(PARTICIPANT_TABLE)
            .insert({
                "session_id": session_id,
                "user_id": user_id,
                "organization_id": organization_id,
                "amount": amount,
                "quantity": quantity,
                "price": price,
                "is_awarded": False,
                "created_at": now
            })
            .execute()
        )

        if not insert_response.data:
            return None

        participant = insert_response.data[0]

        session_repository.increment_pax_registered(session_id)

        log_event(
            action="participant_added",
            session_id=session_id,
            user_id=user_id,
            metadata={"participant_id": participant["id"]}
        )

        return participant

    # ---------------------------------------------------------
    #  🔥 MÉTODO NUEVO — Añadir participante de PRUEBA
    # ---------------------------------------------------------
    def add_test_participant(self, session_id: str) -> Optional[Dict]:
        """
        Método exclusivo para el panel administrativo.
        NO existirá en la plataforma real.
        """

        # 1) Cargar sesión
        session = session_repository.get_session_by_id(session_id)
        if not session:
            return None

        if session["pax_registered"] >= session["capacity"]:
            # blindaje
            return None

        now = datetime.utcnow().isoformat()

        # usuario fake controlado
        fake_user = f"test-user-{session['pax_registered']+1}"

        insert_response = (
            supabase.table(PARTICIPANT_TABLE)
            .insert({
                "session_id": session_id,
                "user_id": fake_user,
                "organization_id": session["organization_id"],
                "amount": 0,
                "quantity": 1,
                "price": 0,
                "is_awarded": False,
                "created_at": now
            })
            .execute()
        )

        if not insert_response.data:
            return None

        participant = insert_response.data[0]

        # Incrementamos pax_registered
        session_repository.increment_pax_registered(session_id)

        log_event(
            action="test_participant_added",
            session_id=session_id,
            user_id=fake_user,
            metadata={"participant_id": participant["id"]}
        )

        return participant


# Instancia global
participant_repository = ParticipantRepository()
