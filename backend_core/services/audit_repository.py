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
    """
    url = f"{SUPABASE_URL}/rest/v1/audit_logs"
    headers = _headers()

    payload = {
        "action": action,
        "session_id": session_id,
        "performed_by": performed_by,
        "metadata": metadata or {},
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)

        if not resp.ok:
            st.error(f"[AUDIT] Error al registrar auditoría ({resp.status_code}).")
            return None

        data = resp.json()
        return data[0] if isinstance(data, list) else data

    except Exception as e:
        st.error(f"[AUDIT] Error al registrar auditoría: {e}")
        return None


def fetch_logs() -> list[dict]:
    """
    Lee todos los registros de la tabla audit_logs de Supabase.
    Nunca revienta el panel.
    """
    url = f"{SUPABASE_URL}/rest/v1/audit_logs"
    headers = _headers()

    params = {
        "select": "*",
        "order": "performed_at.desc",
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)

        if not resp.ok:
            st.error(f"[AUDIT] Error al leer auditoría ({resp.status_code})")
            return []

        data = resp.json()
        return data if isinstance(data, list) else []

    except Exception as e:
        st.error(f"[AUDIT] No se pudo conectar para leer auditoría: {e}")
        return []

