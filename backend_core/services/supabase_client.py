import os
import requests
import streamlit as st

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_SERVICE_ROLE"]


def fetch_rows(table: str, params: dict) -> list:
    """
    GET /table?param=value
    """
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for



