"""
supabase_client.py — versión estable para Streamlit Cloud
Usa supabase-py 1.0.5 (compatible con Python 3.11 y Cloud)
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")   # ← usa la ANON KEY

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL o SUPABASE_KEY no están configuradas.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
