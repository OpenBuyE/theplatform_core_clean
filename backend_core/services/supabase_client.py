import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("❌ ERROR: SUPABASE_URL o SUPABASE_KEY no configurados.")

    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

def table(name: str):
    return supabase.table(name)
