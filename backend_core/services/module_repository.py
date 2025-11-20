import streamlit as st
import requests

from backend_core.services.supabase_client import fetch_rows
from backend_core.services.context import get_current_org

SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = st.secrets["SUPABASE_SERVICE_ROLE"]


def _headers() -> dict:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


# -------------------------------------------------
#   MÓDULOS DE SESIÓN
# -------------------------------------------------

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


# -------------------------------------------------
#   SERIES DE SESIÓN
# -------------------------------------------------

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


def create_session_series(payload: dict) -> dict | None:
    """
    Crea una nueva serie de sesión en session_series.
    El payload debe incluir como mínimo:
        - code
        - name
        - module_id
    y opcionalmente:
        - product_id
        - product_description
        - unit_price
        - currency
        - max_pax
        - activation_threshold
        - location
    """
    org_id = get_current_org()
    if not org_id:
        st.error("No hay organización activa para crear series.")
        return None

    url = f"{SUPABASE_URL}/rest/v1/session_series"
    headers = _headers()

    body = payload.copy()
    body["organization_id"] = org_id

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=10)

        if not resp.ok:
            st.error(f"Error al crear la serie de sesión ({resp.status_code}).")
            # st.write(resp.text)
            return None

        data = resp.json()
        if isinstance(data, list) and data:
            return data[0]
        return data

    except Exception as e:
        st.error(f"Error al conectar para crear la serie: {e}")
        return None

