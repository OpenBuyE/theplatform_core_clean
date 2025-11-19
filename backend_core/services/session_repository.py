from backend_core.services.supabase_client import fetch_rows, update_row


def get_sessions() -> list[dict]:
    """
    Sesiones en estado 'parked'
    """
    params = {
        "select": "*",
        "status": "eq.parked",
    }
    return fetch_rows("sessions", params)


def get_active_sessions() -> list[dict]:
    """
    Sesiones activas
    """
    params = {
        "select": "*",
        "status": "in.(active,open,running)",
    }
    return fetch_rows("sessions", params)


def get_chains() -> list[dict]:
    """
    Sesiones que forman parte de una cadena
    """
    params = {
        "select": "*",
        "chain_group_id": "is.not.null",
    }
    return fetch_rows("sessions", params)


def activate_session(session_id: str):
    """
    Activar sesión (UPDATE status = 'active')
    """
    return update_row("sessions", session_id, {"status": "active"})

