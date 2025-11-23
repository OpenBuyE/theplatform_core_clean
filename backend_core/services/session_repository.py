# backend_core/services/session_repository.py

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Dict, Optional

from backend_core.services import supabase_client
from backend_core.services.audit_repository import AuditRepository

SESSION_TABLE = "ca_sessions"
PARTICIPANTS_TABLE = "ca_session_participants"
SERIES_TABLE = "ca_session_series"


audit = AuditRepository()


# -----------------------------------------------------
# CREACIÓN Y ACTIVACIÓN DE SESIONES
# -----------------------------------------------------

def create_parked_session(
    series_id: str,
    product_id: str,
    organization_id: str,
    capacity: int,
    expires_days: int = 5,
) -> Dict:
    expires_at = datetime.utcnow() + timedelta(days=expires_days)

    payload = {
        "series_id": series_id,
        "product_id": product_id,
        "organization_id": organization_id,
        "capacity": capacity,
        "pax_registered": 0,
        "status": "parked",
        "created_at": datetime.utcnow().isoformat(),
        "activated_at": None,
        "expires_at": expires_at.isoformat(),
        "finished_at": None,
    }

    resp = supabase_client.table(SESSION_TABLE).insert(payload).execute()
    row = resp.data[0]

    audit.log(
        action="SESSION_CREATED_PARKED",
        session_id=row["id"],
        user_id=None,
        metadata={"series_id": series_id, "capacity": capacity},
    )

    return row


def activate_session(session_id: str) -> Dict:
    now = datetime.utcnow().isoformat()

    resp = (
        supabase_client.table(SESSION_TABLE)
        .update({"status": "active", "activated_at": now})
        .eq("id", session_id)
        .execute()
    )
    row = resp.data[0]

    audit.log(
        action="SESSION_ACTIVATED",
        session_id=session_id,
        user_id=None,
        metadata={},
    )

    return row


# -----------------------------------------------------
# CONSULTAS DE SESIONES
# -----------------------------------------------------

def get_session(session_id: str) -> Optional[Dict]:
    resp = (
        supabase_client.table(SESSION_TABLE)
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )
    return resp.data


def get_parked_sessions() -> List[Dict]:
    resp = (
        supabase_client.table(SESSION_TABLE)
        .select("*")
        .eq("status", "parked")
        .order("created_at")
        .execute()
    )
    return resp.data or []


def get_active_sessions() -> List[Dict]:
    resp = (
        supabase_client.table(SESSION_TABLE)
        .select("*")
        .eq("status", "active")
        .order("activated_at")
        .execute()
    )
    return resp.data or []


# -----------------------------------------------------
# PARTICIPANTES
# -----------------------------------------------------

def add_participant(
    session_id: str,
    user_id: str,
    amount: float,
    price: float,
    quantity: int,
    organization_id: str,
) -> Dict:

    payload = {
        "session_id": session_id,
        "user_id": user_id,
        "organization_id": organization_id,
        "amount": amount,
        "price": price,
        "quantity": quantity,
        "is_awarded": False,
        "created_at": datetime.utcnow().isoformat(),
    }

    resp = (
        supabase_client.table(PARTICIPANTS_TABLE)
        .insert(payload)
        .execute()
    )

    # Update pax_registered
    supabase_client.table(SESSION_TABLE).update(
        {"pax_registered": supabase_client.rpc(
            "increment_session_pax", {"sessionid": session_id}
        ).execute().data}
    ).eq("id", session_id).execute()

    audit.log(
        action="PARTICIPANT_ADDED",
        session_id=session_id,
        user_id=user_id,
        metadata={"amount": amount, "price": price},
    )

    return resp.data[0]


def get_participants(session_id: str) -> List[Dict]:
    resp = (
        supabase_client.table(PARTICIPANTS_TABLE)
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )
    return resp.data or []


# -----------------------------------------------------
# FINALIZACIÓN DE SESIONES
# -----------------------------------------------------

def finish_session(session_id: str) -> None:
    now = datetime.utcnow().isoformat()

    supabase_client.table(SESSION_TABLE).update(
        {"status": "finished", "finished_at": now}
    ).eq("id", session_id).execute()

    audit.log(
        action="SESSION_FINISHED",
        session_id=session_id,
        user_id=None,
        metadata={},
    )
