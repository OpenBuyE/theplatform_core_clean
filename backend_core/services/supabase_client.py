import os
from dotenv import load_dotenv
from postgrest import SyncClient

# ============================================================
# CARGA DE VARIABLES DE ENTORNO
# ============================================================
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("❌ ERROR: No están definidas SUPABASE_URL o SUPABASE_SERVICE_KEY.")

# Endpoint REST de Supabase
REST_URL = f"{SUPABASE_URL}/rest/v1"

# Cliente PostgREST (sin proxys raros, sin SDK supabase)
_client = SyncClient(
    REST_URL,
    headers={
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    },
)


# ============================================================
# ACCESO RÁPIDO A TABLAS
# ============================================================
def table(name: str):
    """
    Devuelve un builder de PostgREST para la tabla indicada.

    Ejemplos de uso en services:
      table("products_v2").select("*").eq("id", product_id).single().execute()
      table("ca_sessions").insert({...}).execute()
    """
    return _client.from_(name)
