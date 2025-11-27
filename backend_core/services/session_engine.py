import datetime
from backend_core.services.supabase_client import table
from backend_core.services.session_repository import (
    create_session,
    finish_session,
    get_session_by_id,
)
from backend_core.services.audit_repository import log_event


# ===========================================================
# 🔹 Crear siguiente sesión en una serie
# ===========================================================

def create_next_session_in_series(series_id: str, product_id: str, capacity: int):
    """
    Crea una nueva sesión dentro de una serie (chain/rolling).
    """
    new_id = create_session(product_id, capacity, series_id=series_id)

    log_event(
        "series_spawn",
        series_id=series_id,
        new_session_id=new_id
    )

    return new_id


# ===========================================================
# 🔹 Legacy: get_next_session_in_series (solo para Engine Monitor)
# ===========================================================

def get_next_session_in_series(series_id: str):
    """
    función legacy.
    Engine Monitor la pide pero ya no se usa en el motor moderno.
    Devolvemos una estructura vacía segura.
    """
    return {
        "series_id": series_id,
        "next_session": None,
        "legacy": True,
        "details": "No longer used in deterministic engine."
    }


# ===========================================================
# 🔹 Avanzar una serie (rolling)
# ===========================================================

def advance_series(series_id: str):
    """
    Marca como finalizada la sesión actual y genera la siguiente.
    """
    now = datetime.datetime.utcnow().isoformat()

    # Buscar la sesión activa actual
    current = (
        table("ca_sessions")
        .select("*")
        .eq("series_id", series_id)
        .eq("status", "active")
        .maybe_single()
        .execute()
    )

    if not current:
        return None

    finish_session(current["id"])

    new_session_id = create_next_session_in_series(
        series_id,
        current["product_id"],
        current["capacity"]
    )

    return {
        "old_session": current["id"],
        "new_session": new_session_id,
        "timestamp": now
    }
