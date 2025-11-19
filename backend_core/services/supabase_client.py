import requests
import streamlit as st

# Leemos URL y clave de Supabase desde los secrets de Streamlit
SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
SUPABASE_SERVICE_ROLE = st.secrets["SUPABASE_SERVICE_ROLE"]

BASE_REST_URL = f"{SUPABASE_URL}/rest/v1"


def fetch_rows(table: str, params: dict) -> list[dict]:
    """
    Llama a la REST API de Supabase y devuelve una lista de filas (dict).
    """
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE}",
        "Content-Type": "application/json",
    }

    resp = requests.get(
        f"{BASE_REST_URL}/{table}",
        headers=headers,
        params=params,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


