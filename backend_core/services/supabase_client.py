import os
from functools import lru_cache

from supabase import create_client, Client


def _get_supabase_url_and_key() -> tuple[str, str]:
    """
    Lee la configuración de Supabase desde variables de entorno.

    En Streamlit Cloud configuraremos:
      SUPABASE_URL
      SUPABASE_ANON_KEY

    (Más adelante, si quieres, podemos añadir soporte para SERVICE_ROLE_KEY).
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise RuntimeError(
            "Supabase no está configurado. "
            "Asegúrate de definir SUPABASE_URL y SUPABASE_ANON_KEY en el entorno."
        )

    return url, key


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Devuelve un cliente Supabase cacheado (singleton sencillo)."""
    url, key = _get_supabase_url_and_key()
    return create_client(url, key)
