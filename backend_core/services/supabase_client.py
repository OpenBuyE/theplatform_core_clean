import requests
import streamlit as st

# Leemos configuración desde los secrets de Streamlit
SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")  # por si viene con /
SUPABASE_KEY = st.secrets["SUPABASE_SERVICE_ROLE"]


def _build_headers() -> dict:
    """
    Cabeceras comunes para todas las llamadas a Supabase / PostgREST.
    """
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def fetch_rows(table: str, params: dict) -> list[dict]:
    """
    Realiza un GET a PostgREST y devuelve filas como lista de dicts.
    Si hay error de red o HTTP, muestra el error en Streamlit y devuelve [].

    Esto evita que el panel reviente por errores en Supabase.
    """
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = _build_headers()

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)

        if not resp.ok:
            # Mostramos un error visible en el panel, pero no rompemos la app.
            st.error(
                f"Error al obtener datos de Supabase "
                f"(tabla '{table}', status {resp.status_code})."
            )
            # Opcional: mostrar más detalle técnico en modo depuración
            # st.write(resp.text)
            return []

        data = resp.json()
        # Nos aseguramos de devolver siempre una lista
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            return []

    except requests.RequestException as e:
        st.error(f"No se pudo conectar con Supabase al leer '{table}': {e}")
        return []


def update_row(table: str, row_id: str, patch: dict) -> dict | None:
    """
    Actualiza una fila en Supabase usando PATCH y devuelve la fila actualizada.
    Usa Prefer=return=representation para que Supabase devuelva el registro.

    Si hay error de red o HTTP, muestra el error y devuelve None.
    """
    url = f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{row_id}"
    headers = _build_headers()
    # Prefer: return=representation -> Supabase devuelve el registro modificado
    headers["Prefer"] = "return=representation"

    try:
        resp = requests.patch(url, headers=headers, json=patch, timeout=10)

        if not resp.ok:
            st.error(
                f"Error al actualizar en Supabase "
                f"(tabla '{table}', id={row_id}, status {resp.status_code})."
            )
            # st.write(resp.text)  # si quieres ver detalle técnico
            return None

        data = resp.json()
        if isinstance(data, list) and data:
            return data[0]
        elif isinstance(data, dict):
            return data
        else:
            return None

    except requests.RequestException as e:
        st.error(f"No se pudo conectar con Supabase al actualizar '{table}': {e}")
        return None




