# backend_core/services/participant_repository.py

from __future__ import annotations

from typing import List, Dict
from uuid import uuid4

from backend_core.services import supabase_client
from backend_core.services.audit_repository import log_event

PARTICIPANTS_TABLE = "ca_session_participants"


def add_test_participant(session_id: str) -> Dict:
    """
    Añade un participante de prueba a una sesión.
    No pide user_id, genera uno de test automáticamente.
    """

    data = {
        "session_id": session_id,
        "user_id": f"test-user-{uuid4()}",
        "organization_id": "00000000-0000-0000-0000-000000000001",
        "amount": 1,
        "price": 1,
        "quantity": 1,
        "is_awarded": False,
    }

    resp = supabase_client.table(PARTICIPANTS_TABLE).insert(data).execute()
    row = resp.data[0]

    log_event(
        "participant_added_test",
        session_id=session_id,
        metadata={"participant_id": row["id"], "user_id": row["user_id"]},
    )

    return row


def get_participants_for_session(session_id: str) -> List[Dict]:
    """
    Devuelve todos los participantes de una sesión.
    """

    resp = (
        supabase_client.table(PARTICIPANTS_TABLE)
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )
    return resp.data or []


def mark_awarded(participant_id: str) -> None:
    """
    Marca un participante como adjudicatario (is_awarded = True).
    """

    supabase_client.table(PARTICIPANTS_TABLE).update(
        {"is_awarded": True}
    ).eq("id", participant_id).execute()

    log_event(
        "participant_marked_awarded",
        session_id=None,
        metadata={"participant_id": participant_id},
    )
