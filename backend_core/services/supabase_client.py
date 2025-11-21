"""
supabase_client.py
Cliente estable para Supabase usando librerías oficiales:
postgrest + gotrue + storage3 + supafunc

Compatible con Streamlit Cloud y Python 3.13
"""

import os
from dotenv import load_dotenv
from postgrest import SyncPostgrestClient

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("SUPABASE_URL o SUPABASE_KEY no están definidas.")

# Base URL for the REST API (postgrest endpoint)
REST_URL = SUPABASE_URL.rstrip("/") + "/rest/v1"

# Cliente PostgREST (el que usamos para .select() .insert() .update())
supabase = SyncPostgrestClient(
    REST_URL,
    headers={
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
    },
)
