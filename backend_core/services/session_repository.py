import datetime
from backend_core.services.supabase_client import table


# =====================================================================
# 🔹 UTILIDAD BASE
# =====================================================================

def _extract(result):
    """Normaliza respuesta de Supabase."""
    if isinstance(result, list):
        return result
    return result.get("data", [])


# =====================================================================
# 🔹 CRUD PRINCIPAL DE SESIONES
# =====================================================================

def create_session(data: dict):
    """
    Crea una sesión en ca_sessions.
    data debe incluir product_id, capacity, country, module_id opcional…
    """
    result = table("ca_sessions").insert(data).execute()
    return _extract(result)


def update_session(session_id: str, fields: dict):
    """
    Actualiza cualquier campo de una sesión.
    """
    result = (
        table("ca_sessions")
        .update(fields)
        .eq("id", session_id)
        .execute()
    )
    return _extract(result)


def get_session_by_id(session_id: str):
    result = (
        table("ca_sessions")
        .select("*")
        .eq("id", session_id)
        .maybe_single()
        .execute()
    )
    return result if isinstance(result, dict) else result.get("data")


def get_sessions():
    """
    Alias legacy para obtener todas las sesiones.
    """
    result = table("ca_sessions").select("*").execute()
    return _extract(result)


# =====================================================================
# 🔹 SESIONES POR ESTADO
# =====================================================================

def get_active_sessions():
    """
    Devuelve sesiones activas.
    """
    result = (
        table("ca_sessions")
        .select("*")
        .eq("status", "active")
        .execute()
    )
    return _extract(result)


def get_finished_sessions():
    result = (
        table("ca_sessions")
        .select("*")
        .eq("status", "finished")
        .execute()
    )
    return _extract(result)


def get_expired_sessions():
    """
    Sesiones cuyo expiry_at ya pasó.
    """
    now = datetime.datetime.utcnow().isoformat()
    result = (
        table("ca_sessions")
        .select("*")
        .lt("expiry_at", now)
        .execute()
    )
    return _extract(result)


# =====================================================================
# 🔹 ACTUALIZACIÓN DE ESTADO
# =====================================================================

def finish_session(session_id: str):
    """
    Cambia estado a 'finished'
    """
    return update_session(session_id, {"status": "finished"})


def mark_session_finished(session_id: str):
    """
    Alias legacy
    """
    return finish_session(session_id)


def activate_session(session_id: str):
    """
    Cambia estado a 'active' (legacy)
    """
    return update_session(session_id, {"status": "active"})


# =====================================================================
# 🔹 PARTICIPANTES
# =====================================================================

def get_participants_for_session(session_id: str):
    result = (
        table("ca_participants")
        .select("*")
        .eq("session_id", session_id)
        .execute()
    )
    return _extract(result)


def get_participants_sorted(session_id: str):
    """
    Usado por el adjudicator antiguo.
    """
    result = (
        table("ca_participants")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .execute()
    )
    return _extract(result)


# =====================================================================
# 🔹 SERIES (Cadenas de sesiones consecutivas)
# =====================================================================

def get_sessions_by_series(series_id: str):
    result = (
        table("ca_sessions")
        .select("*")
        .eq("series_id", series_id)
        .order("created_at")
        .execute()
    )
    return _extract(result)


def get_session_series(series_id: str):
    """
    Alias legacy para series.
    """
    return get_sessions_by_series(series_id)


def get_next_session_in_series(series_id: str, current_session_id: str):
    """
    Devuelve la siguiente sesión en la serie.
    """
    series = get_sessions_by_series(series_id)
    ids = [s["id"] for s in series]

    if current_session_id not in ids:
        return None

    idx = ids.index(current_session_id)
    if idx + 1 < len(ids):
        return series[idx + 1]
    return None


# =====================================================================
# 🔹 LISTADO GLOBAL — ENGINE MONITOR
# =====================================================================

def get_all_sessions():
    """
    Usado por Engine Monitor.
    """
    result = table("ca_sessions").select("*").execute()
    return _extract(result)
