# backend_core/services/session_repository.py

from datetime import datetime, timedelta
from backend_core.services.supabase_client import table
from backend_core.services.operator_repository import ensure_country_filter


# ============================================================
# CREAR SESIÓN PARKED
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


# Alias legacy para compatibilidad
create_parked_session = create_session


# ============================================================
# LISTAR SESIONES PARKED
# ============================================================

def get_parked_sessions(operator=None):
    if operator:
        field, countries = ensure_country_filter(operator)
        return (
            table("ca_sessions")
            .select("*")
            .eq("status", "parked")
            .in_(field, countries)
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
# SESIONES ACTIVAS
# ============================================================

def get_active_sessions(operator=None):
    if operator:
        field, countries = ensure_country_filter(operator)
        return (
            table("ca_sessions")
            .select("*")
            .eq("status", "active")
            .in_(field, countries)
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
# LISTAR PARTICIPANTES DE UNA SESIÓN
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
# CADENAS / SERIES
# ============================================================

def get_session_series(session_id, operator=None):
    session = (
        table("ca_sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )

    if not session or not session.get("series"):
        return []

    series = session["series"]

    if operator:
        field, countries = ensure_country_filter(operator)
        return (
            table("ca_sessions")
            .select("*")
            .eq("series", series)
            .in_(field, countries)
            .order("created_at", desc=True)
            .execute()
        )

    return (
        table("ca_sessions")
        .select("*")
        .eq("series", series)
        .order("created_at", desc=True)
        .execute()
    )


# ============================================================
# SESIONES FINALIZADAS
# ============================================================

def get_finished_sessions(operator=None):
    if operator:
        field, countries = ensure_country_filter(operator)
        return (
            table("ca_sessions")
            .select("*")
            .eq("status", "finished")
            .in_(field, countries)
            .order("finished_at", desc=True)
            .execute()
        )

    return (
        table("ca_sessions")
        .select("*")
        .eq("status", "finished")
        .order("finished_at", desc=True)
        .execute()
    )


# ============================================================
# EXPIRADAS (más de 5 días)
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


# ============================================================
# SESIONES (GENÉRICO)
# ============================================================

def get_sessions(operator=None):
    if operator:
        field, countries = ensure_country_filter(operator)
        return (
            table("ca_sessions")
            .select("*")
            .in_(field, countries)
            .order("created_at", desc=True)
            .execute()
        )

    return (
        table("ca_sessions")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )


# ============================================================
# OBTENER SESIÓN POR ID
# ============================================================

def get_session_by_id(session_id):
    return (
        table("ca_sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )
