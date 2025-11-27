# backend_core/services/session_repository.py

from datetime import datetime, timedelta
from uuid import uuid4

from backend_core.services.supabase_client import table
from backend_core.services.operator_repository import ensure_country_filter


# ============================================================
# CREAR SESIÓN PARKED
# ============================================================

def create_parked_session(product_id: str, capacity: int):
    session_id = str(uuid4())

    record = {
        "id": session_id,
        "product_id": product_id,
        "capacity": capacity,
        "pax_registered": 0,
        "status": "parked",
        "created_at": datetime.utcnow().isoformat(),
        "activated_at": None,
        "finished_at": None,
    }

    table("ca_sessions").insert(record).execute()
    return session_id


# ============================================================
# ACTIVAR SESIÓN
# ============================================================

def activate_session(session_id: str):
    return (
        table("ca_sessions")
        .update({"status": "active", "activated_at": datetime.utcnow().isoformat()})
        .eq("id", session_id)
        .execute()
    )


# ============================================================
# FINALIZAR SESIÓN (manual)
# ============================================================

def finish_session(session_id: str):
    """
    Marca una sesión como finished.
    """
    return (
        table("ca_sessions")
        .update({"status": "finished", "finished_at": datetime.utcnow().isoformat()})
        .eq("id", session_id)
        .execute()
    )


# ============================================================
# LISTADOS POR ESTADO
# ============================================================

def get_parked_sessions():
    return (
        table("ca_sessions")
        .select("*")
        .eq("status", "parked")
        .order("created_at", asc=True)
        .execute()
    )


def get_active_sessions():
    return (
        table("ca_sessions")
        .select("*")
        .eq("status", "active")
        .order("activated_at", asc=True)
        .execute()
    )


def get_finished_sessions():
    return (
        table("ca_sessions")
        .select("*")
        .eq("status", "finished")
        .order("finished_at", asc=False)
        .execute()
    )


# ============================================================
# SESSIONS BY SERIES
# ============================================================

def get_sessions_by_series(series_id: str):
    return (
        table("ca_sessions")
        .select("*")
        .eq("series_id", series_id)
        .order("created_at", asc=True)
        .execute()
    )


# ============================================================
# GENERIC LISTING (para Pro dashboards)
# ============================================================

def get_sessions():
    """
    Lista TODAS las sesiones.
    Equivalente a una API REST GET /sessions
    """
    return (
        table("ca_sessions")
        .select("*")
        .order("created_at", asc=False)
        .execute()
    )


def get_all_sessions():
    return get_sessions()


# ============================================================
# PARTICIPANTES
# ============================================================

def get_participants_for_session(session_id: str):
    return (
        table("ca_participants")
        .select("*")
        .eq("session_id", session_id)
        .order("joined_at", asc=True)
        .execute()
    )


def get_participants_sorted(session_id: str):
    """
    Ordena por created_at ascending (usado en adjudicator)
    """
    return (
        table("ca_participants")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", asc=True)
        .execute()
    )


# ============================================================
# EXPIRED SESSIONS (sesiones superan 5 días)
# ============================================================

def get_expired_sessions():
    limit_date = datetime.utcnow() - timedelta(days=5)
    iso = limit_date.isoformat()

    return (
        table("ca_sessions")
        .select("*")
        .lte("created_at", iso)
        .eq("status", "parked")
        .execute()
    )
