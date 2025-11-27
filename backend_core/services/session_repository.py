# backend_core/services/session_repository.py

from datetime import datetime, timedelta
from backend_core.services.supabase_client import table
from backend_core.services.operator_repository import ensure_country_filter


# ============================================================
# SESIONES — HELPERS BASE
# ============================================================

def get_session_by_id(session_id: str):
    return table("ca_sessions").select("*").eq("id", session_id).single().execute()


# ============================================================
# CREACIÓN, ACTIVACIÓN, FINALIZACIÓN
# ============================================================

def create_session(product_id: str, capacity: int, country: str):
    now = datetime.utcnow().isoformat()

    session = {
        "product_id": product_id,
        "capacity": capacity,
        "pax_registered": 0,
        "status": "parked",
        "created_at": now,
        "expires_at": (datetime.utcnow() + timedelta(days=5)).isoformat(),
        "country": country,
    }

    result = table("ca_sessions").insert(session).execute()
    return result[0]["id"]


def activate_session(session_id: str):
    table("ca_sessions").update({"status": "active"}).eq("id", session_id).execute()


def finish_session(session_id: str):
    """Usado por Active Sessions."""
    table("ca_sessions").update({"status": "finished"}).eq("id", session_id).execute()


def mark_session_finished(session_id: str):
    """Usado por adjudicator_engine."""
    table("ca_sessions").update({"status": "finished"}).eq("id", session_id).execute()


# ============================================================
# SELECTORES — LISTADOS DE SESIONES
# ============================================================

def get_sessions(operator=None):
    """Usado por Operator Dashboard Pro."""
    if operator:
        flt = ensure_country_filter(operator)
        return table("ca_sessions").select("*").filter(*flt).order("created_at", desc=True).execute()
    return table("ca_sessions").select("*").order("created_at", desc=True).execute()


def get_all_sessions():
    """Usado por Engine Monitor."""
    return table("ca_sessions").select("*").order("created_at", desc=True).execute()


def get_parked_sessions(operator=None):
    if operator:
        flt = ensure_country_filter(operator)
        return table("ca_sessions").select("*").eq("status", "parked").filter(*flt).execute()
    return table("ca_sessions").select("*").eq("status", "parked").execute()


def get_active_sessions(operator=None):
    if operator:
        flt = ensure_country_filter(operator)
        return table("ca_sessions").select("*").eq("status", "active").filter(*flt).execute()
    return table("ca_sessions").select("*").eq("status", "active").execute()


def get_finished_sessions(operator=None):
    if operator:
        flt = ensure_country_filter(operator)
        return table("ca_sessions").select("*").eq("status", "finished").filter(*flt).execute()
    return table("ca_sessions").select("*").eq("status", "finished").execute()


def get_expired_sessions():
    now = datetime.utcnow().isoformat()
    return table("ca_sessions").select("*").eq("status", "parked").lt("expires_at", now).execute()


# ============================================================
# PARTICIPANTES (ordenados determinísticamente)
# ============================================================

def get_participants_sorted(session_id: str):
    return (
        table("session_participants")
        .select("*")
        .eq("session_id", session_id)
        .order("user_id", asc=True)
        .execute()
    )


# ============================================================
# SERIES DE SESIONES
# ============================================================

def get_session_series():
    """Usado por Admin Series."""
    return table("ca_session_series").select("*").order("created_at").execute()


def list_session_series():
    """Llamado por algunas vistas antiguas."""
    return table("ca_session_series").select("*").order("created_at").execute()


def get_sessions_by_series(series_id: str):
    return (
        table("ca_sessions")
        .select("*")
        .eq("series_id", series_id)
        .order("created_at")
        .execute()
    )


def get_next_session_in_series(series_id: str):
    sessions = get_sessions_by_series(series_id)
    if not sessions:
        return None
    return sessions[-1]


# ============================================================
# ROLLING — CREAR SIGUIENTE SESIÓN
# ============================================================

def create_next_session(old_session):
    new_session = {
        "product_id": old_session["product_id"],
        "capacity": old_session["capacity"],
        "pax_registered": 0,
        "status": "parked",
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(days=5)).isoformat(),
        "series_id": old_session.get("series_id"),
        "country": old_session["country"],
    }
    result = table("ca_sessions").insert(new_session).execute()
    return result[0]["id"]
