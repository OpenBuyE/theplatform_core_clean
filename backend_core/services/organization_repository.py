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


def list_organizations() -> list[dict]:
    """
    Devuelve todas las organizaciones registradas.
    """
    url = f"{SUPABASE_URL}/rest/v1/organizations"
    headers = _headers()
    params = {"select": "*", "order": "created_at.asc"}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if not resp.ok:
            st.error("No se pudo cargar la lista de organizaciones.")
            return []

        data = resp.json()
        return data if isinstance(data, list) else []

    except Exception as e:
        st.error(f"Error al conectar con Supabase (orgs): {e}")
        return []


def create_organization(name: str) -> dict | None:
    """
    Crea una nueva organización.
    """
    url = f"{SUPABASE_URL}/rest/v1/organizations"
    headers = _headers()
    payload = {"name": name}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)

        if not resp.ok:
            st.error("Error al crear la organización.")
            return None

        data = resp.json()
        return data[0] if isinstance(data, list) else data

    except Exception as e:
        st.error(f"No se pudo crear la organización: {e}")
        return None
