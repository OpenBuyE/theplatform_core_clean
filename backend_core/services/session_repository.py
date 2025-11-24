# backend_core/services/session_repository.py

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Dict, Optional

from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event

SESSION_TABLE = "ca_sessions"


# ============================================================
#  SESIONES: CRUD BÁSICO + OPERACIONES INTERNAS
# ============================================================

def create_parked_session(
    product_id: str,
    organization_id: str,
    series_id: str,
    sequence_number: int,
    capacity: int,
    expires_in_days: int = 5,
    module_code: str = "A_DETERMINISTIC",
    module_id: Optional[str] = None,
) -> Dict:
    """
    Crea una sesión en estado 'parked'.

    Ahora soporta module_id (relación con ca_modules).
    """

    expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    data = {
        "product_id": product_id,
        "organization_id": organization_id,
        "series_id": series_id,
        "sequence_number": sequence_number,
        "capacity": capacity,
        "pax_registered": 0,
        "status": "parked",
        "activated_at": None,
        "expires_at": expires_at.isoformat(),
        "finished_at": None,
        "module_code": module_code,
        "module_id": module_id,
    }

    resp = table(SESSION_TABLE).insert(data).execute()
    created = resp.data[0]

    log_event("session_created_parked", session_id=created["id"], metadata=data)

    return created


def activate_session(session_id: str) -> Dict:
    """
    Cambia una sesión parked → active
    """

    now = datetime.utcnow().isoformat()

    resp = (
        table(SESSION_TABLE)
        .update({"status": "active", "activated_at": now})
        .eq("id", session_id)
        .execute()
    )

    updated = resp.data[0]

    log_event("session_activated", session_id=session_id)

    return updated


def get_parked_sessions() -> List[Dict]:
    resp = (
        table(SESSION_TABLE)
        .select("*")
        .eq("status", "parked")
        .order("created_at")
        .execute()
    )
    return resp.data or []


def get_active_sessions() -> List[Dict]:
    resp = (
        table(SESSION_TABLE)
        .select("*")
        .eq("status", "active")
        .order("activated_at")
        .execute()
    )
    return resp.data or []


def get_session_by_id(session_id: str) -> Optional[Dict]:
    resp = table(SESSION_TABLE).select("*").eq("id", session_id).single().execute()
    return resp.data


def increment_pax(session_id: str) -> None:
    """
    Incrementa pax_registered en +1
    """

    s = get_session_by_id(session_id)
    new_value = s["pax_registered"] + 1

    (
        table(SESSION_TABLE)
        .update({"pax_registered": new_value})
        .eq("id", session_id)
        .execute()
    )

    log_event(
        "pax_incremented",
        session_id=session_id,
        metadata={"new_value": new_value},
    )


def finish_session(session_id: str) -> Dict:
    """
    Marca una sesión como finalizada (finished)
    """

    now = datetime.utcnow().isoformat()

    resp = (
        table(SESSION_TABLE)
        .update({"status": "finished", "finished_at": now})
        .eq("id", session_id)
        .execute()
    )

    updated = resp.data[0]

    log_event("session_finished", session_id=session_id)

    return updated


def get_next_session_in_series(series_id: str, after_sequence: int) -> Optional[Dict]:
    """
    Devuelve la siguiente sesión en una serie.
    """

    resp = (
        table(SESSION_TABLE)
        .select("*")
        .eq("series_id", series_id)
        .gt("sequence_number", after_sequence)
        .order("sequence_number")
        .limit(1)
        .execute()
    )

    rows = resp.data or []
    return rows[0] if rows else None

