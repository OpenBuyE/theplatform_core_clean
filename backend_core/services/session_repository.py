# backend_core/services/session_repository.py

from datetime import datetime, timedelta
from backend_core.services.supabase_client import table
from backend_core.services.operator_repository import ensure_country_filter


# ============================================================
#  UTILIDADES INTERNAS
# ============================================================

def _now():
    return datetime.utcnow().isoformat()


# ============================================================
#  CREAR SESIÓN (PARKED)
# ============================================================

def create_session(product_id: str, capacity: int, operator=None):
    """
    Crea una sesión en estado 'parked'.
    """
    payload = {
        "product_id": product_id,
        "capacity": capacity,
        "pax_registered": 0,
        "status": "parked",
        "created_at": _now(),
    }

    # Si aplica filtro de país, asignar país de creación
    if operator:
        _, countries = ensure_country_filter(operator)
        payload["country"] = countries[0]

    res = table("ca_sessions").insert(payload).execute()
    return res[0]["id"] if res else None


def create_parked_session(product_id: str, capacity: int, operator=None):
    return create_session(product_id, capacity, operator)


# ============================================================
#  ACTIVAR SESIÓN
# ============================================================

def activate_session(session_id: str):
    return (
        table("ca_sessions")
        .update({
            "status": "active",
            "activated_at": _now(),
        })
        .eq("id", session_id)
        .execute()
    )


# ============================================================
#  FINALIZAR SESIÓN
# ============================================================

def mark_session_finished(session_id: str):
    return (
        table("ca_sessions")
        .update({
            "status": "finished",
            "finished_at": _now(),
        })
        .eq("id", session_id)
        .execute()
    )


# ============================================================
#  GET SESSION
# ============================================================

def get_session_by_id(session_id: str):
    return (
        table("ca_sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )


# ============================================================
#  LISTAR SESIONES (MÚLTIPLES FILTROS)
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


def get_parked_sessions(operator=None):
    if operator:
        field, countries = ensure_country_filter(operator)
        return (
            table("ca_sessions")
            .select("*")
            .eq("status", "parked")
            .in_(field, countries)
            .execute()
        )

    return (
        table("ca_sessions")
        .select("*")
        .eq("status", "parked")
        .execute()
    )


def get_active_sessions(operator=None):
    if operator:
        field, countries = ensure_country_filter(operator)
        return (
            table("ca_sessions")
            .select("*")
            .eq("status", "active")
            .in_(field, countries)
            .execute()
        )

    return (
        table("ca_sessions")
        .select("*")
        .eq("status", "active")
        .execute()
    )


def get_finished_sessions():
    return (
        table("ca_sessions")
        .select("*")
        .eq("status", "finished")
        .order("finished_at", desc=True)
        .execute()
    )


def get_expired_sessions():
    return (
        table("ca_sessions")
        .select("*")
        .eq("status", "expired")
        .order("created_at", desc=True)
        .execute()
    )


# ============================================================
#  SESSION SERIES
# ============================================================

def get_session_series(series_id: str):
    return (
        table("ca_session_series")
        .select("*")
        .eq("id", series_id)
        .single()
        .execute()
    )


def get_sessions_by_series(series_id: str):
    return (
        table("ca_sessions")
        .select("*")
        .eq("series_id", series_id)
        .order("created_at", desc=True)
        .execute()
    )


def get_next_session_in_series(series_id: str):
    return (
        table("ca_sessions")
        .select("*")
        .eq("series_id", series_id)
        .eq("status", "parked")
        .order("created_at", asc=True)
        .limit(1)
        .execute()
    )


# ============================================================
#  PARTICIPANTES
# ============================================================

def get_participants_for_session(session_id: str):
    return (
        table("ca_session_participants")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", asc=True)
        .execute()
    )


def get_participants_sorted(session_id: str):
    """
    Usado por adjudicator_engine.
    Orden lexicográfico por ID.
    """
    return (
        table("ca_session_participants")
        .select("*")
        .eq("session_id", session_id)
        .order("id", asc=True)
        .execute()
    )


# ============================================================
#  LISTA COMPLETA PARA ENGINE MONITOR
# ============================================================

def get_all_sessions():
    return (
        table("ca_sessions")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
