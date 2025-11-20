"""
supabase_client.py
Cliente HTTP para Supabase totalmente compatible con Python 3.13,
Streamlit Cloud y sin requerir el SDK oficial.

Realiza llamadas directas a la REST API oficial de Supabase.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL y SUPABASE_KEY deben estar configurados.")


class SupabaseHTTPClient:
    def __init__(self):
        self.base_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
        }

    def select(self, table, filters=""):
        url = f"{self.base_url}/{table}?{filters}"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def insert(self, table, data):
        url = f"{self.base_url}/{table}"
        r = requests.post(url, json=data, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def update(self, table, filters, data):
        url = f"{self.base_url}/{table}?{filters}"
        r = requests.patch(url, json=data, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def delete(self, table, filters):
        url = f"{self.base_url}/{table}?{filters}"
        r = requests.delete(url, headers=self.headers)
        r.raise_for_status()
        return True


# Cliente global
supabase = SupabaseHTTPClient()

