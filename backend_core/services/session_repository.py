# ============================================================
# session_repository.py
# Capa completa y estable de gestión de sesiones
# Compatible con todas las vistas del dashboard
# ============================================================

import uuid
from datetime import datetime, timedelta
from backend_core.services.supabase_client import table


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def _now():
    return datetime.utcnow().isoformat()


# ------------------------------------------------------------
# CREATE SESSION (GENÉRICA)
# ------------------------------------------------------------
def create_session(product_id: str, capacity: int, status: str = "parked",
                   module_id: str = None, country: str = "ES",
                   organization_id: str = None):
    """
    Crea una sesión genérica en cualquier estado.
    """
    session_id = str(uuid.uuid4())

    payload = {
        "id": session_id,
        "product_id": product_id,
        "capacity": capacity,
        "pax_registered": 0,
        "status": status,
        "module_id": module_id,
        "country": country,
        "organization_id": organization_id,
        "created_at": _now(),
        "updated_at": _now(),
        "expires_at": (datetime.utcnow() + timedelta(days=5)).isoformat(),
    }

    table("ca_sessions").insert(payload).execute()
    return session_id


# ------------------------------------------------------------
# CREATE PARKED SESSION
# ------------------------------------------------------------
def create_parked_session(product_id: str, capacity: int, country="ES", organization_id=None):
    return create_session(
        product_id=product_id,
        capacity=capacity,
        status="parked",
        country=country,
        organization_id=organization_id
    )


# ------------------------------------------------------------
# ACTIVATE SESSION
# ------------------------------------------------------------
def activate_session(session_id: str):
    """
    Cambia una sesión parked → active.
    """
    return (
        table("ca_sessions")
        .update({
            "status": "active",
            "activated_at": _now(),
            "updated_at": _now()
        })
        .eq("id", session_id)
        .execute()
    )


# ------------------------------------------------------------
# FINISH SESSION (CERRAR)
# ------------------------------------------------------------
def finish_session(session_id: str):
    """
    Marca una sesión como finalizada.
    """
    return (
        table("ca_sessions")
        .update({
            "status": "finished",
            "finished_at": _now(),
            "updated_at": _now()
        })
        .eq("id", session_id)
        .execute()
    )


# ------------------------------------------------------------
# GET SESSION BY ID
# ------------------------------------------------------------
def get_session_by_id(session_id: str):
    result = (
        table("ca_sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )
    return result


# ------------------------------------------------------------
# GET ALL SESSIONS
# ------------------------------------------------------------
def get_all_sessions():
    return table("ca_sessions").select("*").execute() or []


# ------------------------------------------------------------
# PARKED SESSIONS
# ------------------------------------------------------------
def get_parked_sessions(country=None):
    q = table("ca_sessions").select("*").eq("status", "parked")
    if country:
        q = q.eq("country", country)
    return q.execute() or []


# ------------------------------------------------------------
# ACTIVE SESSIONS
# ------------------------------------------------------------
def get_active_sessions(country=None):
    q = table("ca_sessions").select("*").eq("status", "active")
    if country:
        q = q.eq("country", country)
    return q.execute() or []


# ------------------------------------------------------------
# SCHEDULED SESSIONS
# ------------------------------------------------------------
def get_scheduled_sessions(country=None):
    q = table("ca_sessions").select("*").eq("status", "scheduled")
    if country:
        q = q.eq("country", country)
    return q.execute() or []


# ------------------------------------------------------------
# STANDBY SESSIONS
# ------------------------------------------------------------
def get_standby_sessions(country=None):
    q = table("ca_sessions").select("*").eq("status", "standby")
    if country:
        q = q.eq("country", country)
    return q.execute() or []


# ------------------------------------------------------------
# SESSION SERIES
# ------------------------------------------------------------
def get_session_series(product_id: str):
    return (
        table("ca_session_series")
        .select("*")
        .eq("product_id", product_id)
        .execute()
    ) or []


# ------------------------------------------------------------
# PARTICIPANTS
# ------------------------------------------------------------
def get_participants_for_session(session_id: str):
    return (
        table("ca_session_participants")
        .select("*")
        .eq("session_id", session_id)
        .execute()
    ) or []


# ------------------------------------------------------------
# ADD TEST PARTICIPANT
# ------------------------------------------------------------
def add_test_participant(session_id: str, user_id=None):
    participant_id = str(uuid.uuid4())

    payload = {
        "id": participant_id,
        "session_id": session_id,
        "user_id": user_id or ("test_user_" + participant_id[:6]),
        "is_awarded": False,
        "created_at": _now(),
    }

    (
        table("ca_session_participants")
        .insert(payload)
        .execute()
    )

    # Incrementar pax_registered
    table("ca_sessions").update({
        "pax_registered": "pax_registered + 1",
        "updated_at": _now()
    }).eq("id", session_id).execute()

    return participant_id


# ------------------------------------------------------------
# CREATE NEXT SESSION (ROLLING)
# ------------------------------------------------------------
def create_next_session(previous_session):
    return create_session(
        product_id=previous_session["product_id"],
        capacity=previous_session["capacity"],
        status="parked",
        country=previous_session.get("country", "ES"),
        organization_id=previous_session.get("organization_id"),
    )
