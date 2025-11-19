import streamlit as st
import requests

SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = st.secrets["SUPABASE_SERVICE_ROLE"]


def _headers() -> dict:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _get_current_org_id() -> str | None:
    """
    Devuelve la organización activa desde la sesión de Streamlit.
    En el panel el selector de organización debe haber guardado esto en:
    st.session_state["organization_id"]
    """
    return st.session_state.get("organization_id")


def log_action(
    action: str,
    session_id: str,
    performed_by: str,
    metadata: dict | None = None,
):
    """
    Inserta un registro de auditoría en Supabase.
    No rompe el panel si falla: muestra error y continúa.
    """

    url = f"{SUPABASE_URL}/rest/v1/audit_logs"
    headers = _headers()

    payload = {
        "action": action,
        "session_id": session_id,
        "performed_by": performed_by,
        "metadata": metadata or {},
        # Multi-tenant: cada log asociado a una organización
        "organization_id": _get_current_org_id(),
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)

        if not resp.ok:
            st.error(f"[AUDIT] Error al registrar auditoría ({resp.status_code}).")
            # st.write(resp.text)  # opcional para depurar
            return None

        data = resp.json()
        return data[0] if isinstance(data, list) and data else data

    except Exception as e:
        st.error(f"[AUDIT] Error al registrar auditoría: {e}")
        return None


def fetch_logs() -> list[dict]:
    """
    Lee los registros de la tabla audit_logs de Supabase
    filtrados por la organización activa.

    Nunca revienta el panel: si hay problemas, devuelve [].
    """
    org_id = _get_current_org_id()
    if not org_id:
        st.warning("Selecciona una organización para ver los registros de auditoría.")
        return []

    url = f"{SUPABASE_URL}/rest/v1/audit_logs"
    headers = _headers()

    params = {
        "select": "*",
        "order": "performed_at.desc",
        "organization_id": f"eq.{org_id}",
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)

        if not resp.ok:
            st.error(f"[AUDIT] Error al leer auditoría ({resp.status_code})")
            # st.write(resp.text)  # opcional depuración
            return []

        data = resp.json()
        return data if isinstance(data, list) else []

    except Exception as e:
        st.error(f"[AUDIT] No se pudo conectar para leer auditoría: {e}")
        return []

