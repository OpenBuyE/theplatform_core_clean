# backend_core/services/session_repository.py

from datetime import datetime, timedelta
from backend_core.services.supabase_client import table
from backend_core.services.operator_repository import ensure_country_filter


# ============================================================
# CREAR SESIÓN
# ============================================================

def create_session(product_id, capacity, country, module_id=None):
    rec = {
        "product_id": product_id,
        "capacity": capacity,
        "pax_registered": 0,
        "status": "parked",
        "country": country,
        "module_id": module_id,
        "created_at": datetime.utcnow().isoformat(),
    }
    result = table("ca_sessions").insert(rec).execute()
    return result[0]["id"]

create_parked_session = create_session   # alias compatibilidad


# ============================================================
# PARKED
# ============================================================

def get_parked_sessions(operator=None):
    if operator:
        field, allowed = ensure_country_filter(operator)
        return (
            table("ca_sessions")
            .select("*")
            .eq("status", "parked")
            .in_(field, allowed)
            .order("created_at", desc=True)
            .execute()
        )

    return (
        table("ca_sessions")
        .select("*")
        .eq("status", "parked")
        .order("created_at", desc=True)
        .execute()
    )


# ============================================================
# ACTIVAR SESIÓN
# ============================================================

def activate_session(session_id):
    return (
        table("ca_sessions")
        .update({
            "status": "active",
            "activated_at": datetime.utcnow().isoformat()
        })
        .eq("id", session_id)
        .execute()
    )


# ============================================================
# ACTIVAS
# ============================================================

def get_active_sessions(operator=None):
    if operator:
        field, allowed = ensure_country_filter(operator)
        return (
            table("ca_sessions")
            .select("*")
            .eq("status", "active")
            .in_(field, allowed)
            .order("activated_at", desc=True)
            .execute()
        )

    return (
        table("ca_sessions")
        .select("*")
        .eq("status", "active")
        .order("activated_at", desc=True)
        .execute()
    )


# ============================================================
# PARTICIPANTES
# ============================================================

def get_participants_for_session(session_id):
    return (
        table("ca_participants")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", asc=True)
        .execute()
    )


# ============================================================
# SERIES / CHAINS
# ============================================================

def get_session_series(session_id):
    session = (
        table("ca_sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )

    if not session or not session.get("series"):
        return []

    ser = session["series"]

    return (
        table("ca_sessions")
        .select("*")
        .eq("series", ser)
        .order("created_at", desc=True)
        .execute()
    )

# alias compatibilidad
get_sessions_by_series = get_session_series


# ============================================================
# FINALIZADAS
# ============================================================

def get_finished_sessions():
    return (
        table("ca_sessions")
        .select("*")
        .eq("status", "finished")
        .order("finished_at", desc=True)
        .execute()
    )


# ============================================================
# EXPIRADAS (>5 días)
# ============================================================

def get_expired_sessions():
    cutoff = (datetime.utcnow() - timedelta(days=5)).isoformat()
    return (
        table("ca_sessions")
        .select("*")
        .eq("status", "active")
        .lt("activated_at", cutoff)
        .execute()
    )


# ============================================================
# FINALIZAR SESIÓN
# ============================================================

def finish_session(session_id, winner_participant_id=None):
    return (
        table("ca_sessions")
        .update({
            "status": "finished",
            "winner_participant_id": winner_participant_id,
            "finished_at": datetime.utcnow().isoformat(),
        })
        .eq("id", session_id)
        .execute()
    )

# alias compatibilidad
mark_session_finished = finish_session


# ============================================================
# LISTAR TODAS LAS SESIONES (para Engine Monitor)
# ============================================================

def get_all_sessions():
    return (
        table("ca_sessions")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )


# ============================================================
# POR ID
# ============================================================

def get_session_by_id(session_id):
    return (
        table("ca_sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )
