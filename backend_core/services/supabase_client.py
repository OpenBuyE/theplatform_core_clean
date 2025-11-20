"""
supabase_client.py
Cliente Supabase para Compra Abierta.

Compatible con supabase-py moderno.
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL o SUPABASE_KEY no están definidas en el entorno."
    )

# Crear cliente global
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
