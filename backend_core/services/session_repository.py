from backend_core.services.supabase_client import fetch_rows


def get_sessions() -> list[dict]:
    """
    Sesiones en estado 'parked' (Parque de Sesiones).
    """
    params = {
        "select": "*",
        "status": "eq.parked",
    }
    return fetch_rows("sessions", params)


def get_active_sessions() -> list[dict]:
    """
    Sesiones en estado 'active', 'open' o 'running'
    (ajusta los estados a lo que uses realmente).
    """
    # PostgREST usa la sintaxis: campo=in.(valor1,valor2)
    params = {
        "select": "*",
        "status": "in.(active,open,running)",
    }
    return fetch_rows("sessions", params)


def get_chains() -> list[dict]:
    """
    Sesiones que forman parte de una cadena (chain_group_id no nulo).
    """
    # Filtro 'is.not.null' en PostgREST
    params = {
        "select": "*",
        "chain_group_id": "is.not.null",
    }
    return fetch_rows("sessions", params)


