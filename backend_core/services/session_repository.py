from backend_core.services.supabase_client import fetch_rows, update_row


def get_sessions() -> list[dict]:
    """
    Devuelve las sesiones en estado 'parked'.

    Si hay un problema con Supabase, fetch_rows() ya gestionará el error
    y devolverá [] sin romper el panel.
    """
    params = {
        "select": "*",
        "status": "eq.parked",
    }
    return fetch_rows("sessions", params)


def get_active_sessions() -> list[dict]:
    """
    Devuelve las sesiones en estados activos.
    Consideramos activos: active, open, running.
    """
    params = {
        "select": "*",
        "status": "in.(active,open,running)",
    }
    return fetch_rows("sessions", params)


def get_chains() -> list[dict]:
    """
    Devuelve las sesiones que tienen una cadena operativa asociada
    (chain_group_id no nulo).

    Usamos el operador 'not.is.null', que es robusto como filtro en PostgREST.
    """
    params = {
        "select": "*",
        "chain_group_id": "not.is.null",
    }
    return fetch_rows("sessions", params)


def activate_session(session_id: str) -> dict:
    """
    Cambia una sesión de parked → active.

    Si update_row falla y devuelve None, lanzamos una excepción controlada.
    Esto encaja con el try/except que ya tienes en la vista (park_sessions.py),
    que mostrará un mensaje de error en lugar de romper el panel.
    """
    patch = {
        "status": "active"
    }

    updated = update_row("sessions", session_id, patch)

    if updated is None:
        # Esto será capturado por el try/except en la vista y se mostrará st.error
        raise RuntimeError("No se pudo actualizar la sesión en Supabase.")

    return updated

