"""
supabase_client.py
Cliente Supabase vía REST (compatible con Python 3.13 y Streamlit Cloud)
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # ANON KEY !!!

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL y SUPABASE_KEY deben estar definidas.")

# URL base REST (PostgREST)
REST_URL = f"{SUPABASE_URL}/rest/v1"

# Cabeceras standard
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

class SupabaseREST:

    # SELECT
    def select(self, table, params=None):
        url = f"{REST_URL}/{table}"
        res = requests.get(url, headers=HEADERS, params=params)
        res.raise_for_status()
        return res.json()

    # INSERT
    def insert(self, table, data):
        url = f"{REST_URL}/{table}"
        res = requests.post(url, headers=HEADERS, json=data)
        res.raise_for_status()
        return res.json()

    # UPDATE
    def update(self, table, match, data):
        url = f"{REST_URL}/{table}"
        params = {"select": "*", **match}
        res = requests.patch(url, headers=HEADERS, params=params, json=data)
        res.raise_for_status()
        return res.json()

    # DELETE
    def delete(self, table, match):
        url = f"{REST_URL}/{table}"
        res = requests.delete(url, headers=HEADERS, params=match)
        res.raise_for_status()
        return res.json()

# Instancia global para usar en repositorios
supabase = SupabaseREST()
