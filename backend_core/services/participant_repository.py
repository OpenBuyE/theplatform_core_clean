
# backend_core/services/participant_repository.py

from __future__ import annotations
from typing import List, Dict

from backend_core.services import supabase_client
from backend_core.services.audit_repository import log_event

PARTICIPANTS_TABLE = "ca_session_participants"


def add_test_participant(session_id: str, user_id: str):
    data = {
        "session_id": session_id,
        "user_id": user_id,
        "amount": 1,
        "price": 1,
        "quantity": 1,
        "is_awarded": False,
    }
    supabase_client.table(PARTICIPANTS_TABLE).insert(data).execute()

    log_event("participant_added", session_id=session_id, metadata=data)


def get_participants_for_session(session_id: str) -> List[Dict]:
    resp = (
        supabase_client.table(PARTICIPANTS_TABLE)
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )
    return resp.data or []


def mark_awarded(session_id: str, user_id: str):
    supabase_client.table(PARTICIPANTS_TABLE).update(
        {"is_awarded": True}
    ).eq("session_id", session_id).eq("user_id", user_id).execute()

    log_event("participant_awarded", session_id=session_id, metadata={"user_id": user_id})
