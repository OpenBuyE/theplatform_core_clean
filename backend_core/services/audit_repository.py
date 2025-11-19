import streamlit as st
import requests

SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = st.secrets["SUPABASE_SERVICE_ROLE"]


def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def log_action(action: str, session_id: str, performed_by: str, metadata: dict | None = None):
    """
    Inserta un registro de auditoría en Supabase.
    Nunca rompe el panel si falla: muestra error y continúa.
    """

    url = f"{SUPABASE_URL}/rest/v1/audit_logs"
    headers = _headers()

    payload = {
        "action": action,
        "session_id": session_id,
        "performed_by": performed_by,
        "metadata": metadata or {}
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)

        if not resp.ok:
            st.error(f"[AUDIT] Error al registrar auditoría ({resp.status_code}).")
            # st.write(resp.text)
            return None

        data = resp.json()
        return data[0] if isinstance(data, list) else data

    except Exception as e:
        st.error(f"[AUDIT] No se pudo registrar auditoría: {e}")
        return None
