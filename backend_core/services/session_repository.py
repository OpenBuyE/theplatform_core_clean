import datetime
from backend_core.services.supabase_client import table


# ======================================================================
# 📌 Básico — Obtener sesiones por estado
# ======================================================================

def get_sessions(status: str = None):
    q = table("ca_sessions").select("*")

    if status:
        q = q.eq("status", status)

    result = q.execute()
    return result if isinstance(result, list) else result.get("data", [])


def get_session_by_id(session_id: str):
    result = (
        table("ca_sessions")
        .select("*")
        .eq("id", session_id)
        .limit(1)
        .execute()
    )
    if not result:
        return None
    return result[0] if isinstance(result, list) else result.get("data", [None])[0]


def get_finished_sessions():
    result = (
        table("ca_sessions")
        .select("*")
        .eq("status", "finished")
        .execute()
    )
    return result if isinstance(result, list) else result.get("data", [])


def get_expired_sessions():
    result = (
        table("ca_sessions")
        .select("*")
        .eq("status", "expired")
        .execute()
    )
    return result if isinstance(result, list) else result.get("data", [])


def get_sessions_by_series(series_id: str):
    result = (
        table("ca_sessions")
        .select("*")
        .eq("series_id", series_id)
        .execute()
    )
    return result if isinstance(result, list) else result.get("data", [])



# ======================================================================
# 📌 Crear / Actualizar sesiones
# ======================================================================

def create_session(data: dict):
    result = table("ca_sessions").insert(data).execute()
    return result if isinstance(result, list) else result.get("data", [])


def update_session(session_id: str, updates: dict):
    result = (
        table("ca_sessions")
        .update(updates)
        .eq("id", session_id)
        .execute()
    )
    return result if isinstance(result, list) else result.get("data", [])


def finish_session(session_id: str):
    return update_session(session_id, {"status": "finished"})


def mark_session_finished(session_id: str):
    return update_session(session_id, {"status": "finished"})


# ======================================================================
# 📌 Participantes de una sesión
# ======================================================================

def get_participants_for_session(session_id: str):
    result = (
        table("ca_session_participants")
        .select("*")
        .eq("session_id", session_id)
        .execute()
    )
    return result if isinstance(result, list) else result.get("data", [])


# ANTIGUO NOMBRE USADO POR ALGUNAS VISTAS
def get_participants_sorted(session_id: str):
    data = get_participants_for_session(session_id)
    if not data:
        return []

    rows = data if isinstance(data, list) else data.get("data", [])

    try:
        return sorted(rows, key=lambda x: x.get("created_at", ""))
    except Exception:
        return rows



# ======================================================================
# 📌 Engine / Monitor
# ======================================================================

def get_all_sessions():
    result = table("ca_sessions").select("*").execute()
    return result if isinstance(result, list) else result.get("data", [])



# ======================================================================
# 📌 Series (Admin Series / Chains)
# ======================================================================

def get_session_series():
    result = table("ca_series").select("*").execute()
    return result if isinstance(result, list) else result.get("data", [])



# ======================================================================
# 📌 Limpieza de sesiones expiradas
# ======================================================================

def auto_expire_sessions():
    """
    Marca como 'expired' las sesiones cuyo expiry_date ya pasó.
    """
    now = datetime.datetime.utcnow().isoformat()

    sessions = (
        table("ca_sessions")
        .select("*")
        .lte("expiry_date", now)
        .eq("status", "active")
        .execute()
    )

    rows = sessions if isinstance(sessions, list) else sessions.get("data", [])

    for s in rows:
        update_session(s["id"], {"status": "expired"})

    return len(rows)



# ======================================================================
# 📌 Funciones usadas por vistas legacy
# ======================================================================

def get_operator_allowed_countries(operator_id: str):
    """
    Compat: necesario porque algunas vistas antiguas intentan importarla aquí.
    Ahora esto existe realmente en operator_repository, pero lo repetimos.
    """
    from backend_core.services.operator_repository import get_operator_allowed_countries
    return get_operator_allowed_countries(operator_id)
