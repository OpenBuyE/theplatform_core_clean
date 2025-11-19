from backend_core.services.supabase_client import fetch_rows


def get_sessions() -> list[dict]:
    """
    Devuelve sesiones en estado 'parked' (Parque de Sesiones).
    """
    params = {
        "select": "*",
        "status": "eq.parked",
    }
    return fetch_rows("sessions", params)


def get_active_sessions() -> list[dict]:
    """
    Devuelve sesiones activas.
    Estados usados: active, open, running.
    (Ajusta los estados según tu lógica real).
    """
    params = {
        "select": "*",
        "status": "in.(active,open,running)",
    }
    return fetch_rows("sessions", params)


def get_chains() -> list[dict]:
    """
    Devuelve sesiones que pertenecen a una cadena.
    Se filtra por las que tienen chain_group_id no nulo.
    """
    params = {
        "select": "*",
        "chain_group_id": "not.is.null",   # ✔️ Sintaxis correcta para Supabase REST
    }
    return fetch_rows("sessions", params)



