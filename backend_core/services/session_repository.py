# backend_core/services/session_repository.py

from backend_core.services.supabase_client import table
from datetime import datetime, timedelta

# ======================================================================
# 📌 CREAR SESIÓN
# ======================================================================

def create_session(data: dict):
    return table("sessions").insert(data).execute()


def create_parked_session(product_id: str, capacity: int):
    data = {
        "status": "parked",
        "product_id": product_id,
        "capacity": capacity,
        "pax_registered": 0,
        "created_at": datetime.utcnow().isoformat(),
    }
    return create_session(data)[0]["id"]


# ======================================================================
# 📌 SESIONES PARKED / ACTIVE
# ======================================================================

def get_parked_sessions():
    return (
        table("sessions")
        .select("*")
        .eq("status", "parked")
        .order("created_at", desc=True)
        .execute()
    )


def get_active_sessions():
    return (
        table("sessions")
        .select("*")
        .eq("status", "active")
        .order("activated_at", desc=True)
        .execute()
    )


# 📌 LISTA COMPLETA — usado por Operator Dashboard Pro
def get_sessions():
    return (
        table("sessions")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )


def get_session_by_id(session_id: str):
    return (
        table("sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )


# ======================================================================
# 📌 FINALIZAR / ACTIVAR SESIÓN
# ======================================================================

def activate_session(session_id: str):
    return (
        table("sessions")
        .update({
            "status": "active",
            "activated_at": datetime.utcnow().isoformat(),
        })
        .eq("id", session_id)
        .execute()
    )


def finish_session(session_id: str, winner_participant_id: str = None):
    return (
        table("sessions")
        .update({
            "status": "finished",
            "winner_participant_id": winner_participant_id,
            "finished_at": datetime.utcnow().isoformat(),
        })
        .eq("id", session_id)
        .execute()
    )


# ======================================================================
# 📌 PARTICIPANTES — requerido por Active Sessions
# ======================================================================

def get_participants_for_session(session_id: str):
    return (
        table("participants")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .execute()
    )


# ======================================================================
# 📌 SERIES — usado en Session Chains
# ======================================================================

def get_session_series(series_id: str):
    return (
        table("session_series")
        .select("*")
        .eq("id", series_id)
        .single()
        .execute()
    )


def get_sessions_by_series(series_id: str):
    return (
        table("sessions")
        .select("*")
        .eq("series_id", series_id)
        .order("created_at", desc=True)
        .execute()
    )


# ======================================================================
# 📌 EXPIRADAS / HISTÓRICO
# ======================================================================

def get_expired_sessions():
    expiry = datetime.utcnow() - timedelta(days=5)
    return (
        table("sessions")
        .select("*")
        .eq("status", "parked")
        .lte("created_at", expiry.isoformat())
        .execute()
    )


def get_finished_sessions():
    return (
        table("sessions")
        .select("*")
        .eq("status", "finished")
        .order("finished_at", desc=True)
        .execute()
    )


# ======================================================================
# 📌 LISTA GENERAL — Engine Monitor
# ======================================================================

def get_all_sessions():
    return (
        table("sessions")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )


# ======================================================================
# 📌 COMPATIBILIDAD — VISTAS ANTIGUAS
# ======================================================================

def mark_session_finished(session_id: str, winner_participant_id: str = None):
    """
    Alias de compatibilidad para vistas anteriores.
    """
    return finish_session(session_id, winner_participant_id)
