# backend_core/services/session_repository.py

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Dict, Optional

from backend_core.services import supabase_client
from backend_core.services.audit_repository import log_event

SESSIONS_TABLE = "ca_sessions"
PARTICIPANTS_TABLE = "ca_session_participants"


# ============================================================
# SESSION QUERIES
# ============================================================

def get_session_by_id(session_id: str) -> Optional[Dict]:
    resp = (
        supabase_client.table(SESSIONS_TABLE)
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )
    return resp.data


def get_parked_sessions() -> List[Dict]:
    resp = (
        supabase_client.table(SESSIONS_TABLE)
        .select("*")
        .eq("status", "parked")
        .order("created_at")
        .execute()
    )
    return resp.data or []


def get_active_sessions() -> List[Dict]:
    resp = (
        supabase_client.table(SESSIONS_TABLE)
        .select("*")
        .eq("status", "active")
        .order("activated_at")
        .execute()
    )
    return resp.data or []


def get_next_session_in_series(session_id: str):
    """Devuelve la siguiente sesión en la serie (rolling)."""
    session = get_session_by_id(session_id)
    if not session:
        return None

    resp = (
        supabase_client.table(SESSIONS_TABLE)
        .select("*")
        .eq("series_id", session["series_id"])
        .eq("sequence_number", session["sequence_number"] + 1)
        .single()
        .execute()
    )
    return resp.data


# ============================================================
# SESSION STATE UPDATES
# ============================================================

def create_parked_session(data: Dict):
    resp = supabase_client.table(SESSIONS_TABLE).insert(data).execute()
    log_event("session_created", session_id=data.get("id"), metadata=data)
    return resp.data


def activate_session(session_id: str):
    now = datetime.utcnow().isoformat()
    expires = (datetime.utcnow() + timedelta(days=5)).isoformat()

    supabase_client.table(SESSIONS_TABLE).update(
        {
            "status": "active",
            "activated_at": now,
            "expires_at": expires,
        }
    ).eq("id", session_id).execute()

    log_event("session_activated", session_id=session_id)


def finish_session(session_id: str):
    now = datetime.utcnow().isoformat()

    supabase_client.table(SESSIONS_TABLE).update(
        {
            "status": "finished",
            "finished_at": now,
        }
    ).eq("id", session_id).execute()

    log_event("session_finished", session_id=session_id)

