import streamlit as st
import requests

SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = st.secrets["SUPABASE_SERVICE_ROLE"]


def _headers() -> dict:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


# -----------------------------
#        ROLES (helper)
# -----------------------------

def _get_role_id_by_name(role_name: str) -> str | None:
    """
    Busca el id de un rol por su nombre en la tabla roles.
    """
    url = f"{SUPABASE_URL}/rest/v1/roles"
    headers = _headers()
    params = {
        "select": "id",
        "name": f"eq.{role_name}",
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if not resp.ok:
            st.error(f"Error al buscar el rol '{role_name}' ({resp.status_code}).")
            return None

        data = resp.json()
        if not data:
            st.error(f"No se encontró el rol '{role_name}' en la tabla roles.")
            return None

        return data[0]["id"]

    except Exception as e:
        st.error(f"Error al conectar para leer roles: {e}")
        return None


# -----------------------------
#          USUARIOS
# -----------------------------

def list_users() -> list[dict]:
    """
    Devuelve todos los usuarios del sistema.
    """
    url = f"{SUPABASE_URL}/rest/v1/users"
    headers = _headers()
    params = {"select": "*", "order": "created_at.asc"}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if not resp.ok:
            st.error("No se pudo cargar la lista de usuarios.")
            return []

        data = resp.json()
        return data if isinstance(data, list) else []

    except Exception as e:
        st.error(f"Error al conectar con Supabase (users): {e}")
        return []


def create_user(name: str, email: str) -> dict | None:
    """
    Crea un usuario sin asignarlo aún a ninguna organización.
    """
    url = f"{SUPABASE_URL}/rest/v1/users"
    headers = _headers()
    payload = {"name": name, "email": email}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)

        if not resp.ok:
            st.error("Error al crear el usuario.")
            # st.write(resp.text)
            return None

        data = resp.json()
        return data[0] if isinstance(data, list) and data else data

    except Exception as e:
        st.error(f"No se pudo crear el usuario: {e}")
        return None


# -----------------------------
#   ORGANIZATION ↔ USERS
# -----------------------------

def list_users_in_org(org_id: str) -> list[dict]:
    """
    Devuelve usuarios asignados a una organización.

    Hace join entre organization_users y users, y opcionalmente roles.
    """
    if not org_id:
        return []

    url = f"{SUPABASE_URL}/rest/v1/organization_users"
    headers = _headers()

    params = {
        "select": "user_id, role, role_id, users(*), roles(name), created_at",
        "organization_id": f"eq.{org_id}",
