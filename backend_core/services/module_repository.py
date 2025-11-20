import streamlit as st

from backend_core.services.supabase_client import fetch_rows
from backend_core.services.context import get_current_org


def list_session_modules() -> list[dict]:
    """
    Devuelve todos los módulos de sesión definidos en session_modules.
    Ejemplos de code:
        - rolling   (reposición automática)
        - scheduled (programada)
        - standby   (en preparación)
    """
    params = {
        "select": "*",
        "order": "created_at.asc",
    }
    return fetch_rows("session_modules", params)


def list_session_series() -> list[dict]:
    """
    Devuelve todas las series de sesión (session_series)
    de la organización activa.
    """
    org_id = get_current_org()
    if not org_id:
        st.warning("Selecciona una organización para ver las series de sesión.")
        return []

    params = {
        "select": "*",
        "organization_id": f"eq.{org_id}",
        "order": "created_at.asc",
    }
    return fetch_rows("session_series", params)


def get_session_series_by_code(code: str) -> dict | None:
    """
    Devuelve una serie concreta por su código (ej: 'X23')
    dentro de la organización activa.
    """
    org_id = get_current_org()
    if not org_id:
        st.warning("Selecciona una organización para buscar series de sesión.")
        return None

    params = {
        "select": "*",
        "organization_id": f"eq.{org_id}",
        "code": f"eq.{code}",
    }
    rows = fetch_rows("session_series", params)
    if rows:
        return rows[0]
    return None
