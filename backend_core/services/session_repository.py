# backend_core/services/session_repository.py

from backend_core.services.supabase_client import table
from datetime import datetime, timedelta

# ======================================================================
# 📌 CREAR SESIÓN PARKED
# ======================================================================
def create_session(data: dict):
    return table("sessions").insert(data).execute()

def create_parked_session(product_id: str, capacity: int):
    data = {
        "status": "parked",
        "product_id": product_id,
        "capacity": capacity,
        "pax_registered": 0,
    }
    return create_session(data)[0]["id"]


# ======================================================================
# 📌 SESIONES ACTIVAS / PARKED / HISTORY
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

def get_session_by_id(session_id: str):
    return (
        table("sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )


# ======================================================================
# 📌 ACTIVAR SESIÓN
# ======================================================================

def activate_session(session_id: str):
    return (
        table("sessions")
        .update({
            "status": "active",
            "activated_at": datetime.utcnow().isoformat()
        })
        .eq("id", session_id)
        .execute()
    )


# ======================================================================
# 📌 FINALIZAR SESIÓN
# ======================================================================

def finish_session(session_id: str, winner_participant_id: str = None):
    return (
        table("sessions")
        .update({
            "status": "finished",
            "finished_at": datetime.utcnow().isoformat(),
            "winner_participant_id": winner_participant_id,
        })
        .eq("id", session_id)
        .execute()
    )


# ======================================================================
# 📌 SESSION CHAINS
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
# 📌 HISTÓRICAS / EXPIRADAS
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


# ======================================================================
# 📌 LISTA GENERAL
# ======================================================================

def get_all_sessions():
    return (
        table("sessions")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
