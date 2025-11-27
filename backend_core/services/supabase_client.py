import os
from dotenv import load_dotenv
from supabase import Client, create_client

# ============================================================
# CARGA DE VARIABLES DE ENTORNO
# ============================================================
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("❌ ERROR: No están definidas SUPABASE_URL o SUPABASE_SERVICE_KEY.")

# ============================================================
# CLIENTE SUPABASE — OFICIAL Y COMPATIBLE
# ============================================================
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ============================================================
# ACCESO RÁPIDO A TABLAS
# ============================================================
def table(name: str):
    """
    Retorna la tabla de supabase lista para usar:
       table("ca_operators").select("*").execute()
    """
    return supabase.table(name)
