import requests
import streamlit as st

# --- Cargar credenciales desde secrets ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE = st.secrets["SUPABASE_SERVICE_ROLE"]

HEADERS = {
    "apikey": SUPABASE_SERVICE_ROLE,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE}",
}


def fetch_rows(table: str, params: dict) -> list[dict]:
    """
    Consulta GET a Supabase (PostgREST)
    """
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    resp = requests.get(url, headers=HEADERS, params=params)

    resp.raise_for_status()
    return resp.json()


def update_row(table: str, row_id: str, data: dict) -> dict:
    """
    UPDATE en Supabase por ID
    """
    url = f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{row_id}"
    resp = requests.patch(url, headers=HEADERS, json=data)

    resp.raise_for_status()
    return resp.json()



