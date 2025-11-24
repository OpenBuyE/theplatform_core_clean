# backend_core/services/supabase_client.py

from supabase import create_client, Client
import os

# ============================================
# CONFIG SUPABASE (usa variables de entorno)
# ============================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL o SUPABASE_KEY no están configurados en variables de entorno.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ============================================
# API estándar esperada por los repositories
# ============================================

def table(name: str):
    """
    Compatibilidad con el codebase actual:
    hace que supabase_client.table("mi_tabla") funcione.
    """
    return supabase.table(name)
