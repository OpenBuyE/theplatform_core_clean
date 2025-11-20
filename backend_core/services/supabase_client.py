"""
supabase_client.py
Cliente de Supabase para Compra Abierta.

Este archivo crea un cliente global 'supabase' accesible desde
todos los repositorios del backend.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno desde .env (si existe)
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "ERROR: Las variables SUPABASE_URL y SUPABASE_KEY no están definidas. "
        "Crea un archivo .env o configúralas en el entorno."
    )

# Crear cliente global
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)



