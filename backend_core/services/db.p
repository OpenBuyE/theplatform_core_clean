from supabase import create_client
import os

# ======================================================
#  DB CONNECTION WRAPPER — STREAMLIT + SUPABASE
# ======================================================

# Intentamos cargar variables desde entorno Streamlit Cloud
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "❌ ERROR: No se han definido SUPABASE_URL o SUPABASE_SERVICE_KEY en el entorno."
    )

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
