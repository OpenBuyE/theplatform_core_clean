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


# -------------------------------------------------
#   ROLES (helper)
# -------------------------------------------------

def _get_role_id_by_name(role_name: str) -> str | None:
    url = f"{SUPABASE_URL}/rest/v1/roles"
    params = {
        "select": "id",
        "name": f"eq.{role_name}",
    }

    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=10)
        if not resp.ok:
            st.error(f"Error al buscar el rol '{role_name}' ({resp.status_code})")
            return None

        data = resp.json()
        if data:
            return data[0]["id"]
        return None

    except Exception as e:
        st.error(f"Error al conectar para leer roles: {e}")
        return None


# -------------------------------------------------
#   USUARIOS
# -------------------------------------------------

def list_users() -> list[dict]:
    url = f"{SUPABASE_URL}/rest/v1/users"
    params = {"select": "*", "order": "created_at.asc"}

    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=10)
        if not resp.ok:
            st.error("No se pudo cargar la lista de usuarios.")
            return []

        data = resp.json()
        return data if isinstance(data, list) else []

    except Exception as e:
        st.error(f"Error al conectar con Supabase (users): {e}")
        return []


def create_user(name: str, email: str) -> dict | None:
    url = f"{SUPABASE_URL}/rest/v1/users"
    payload = {
        "name": name,
        "email": email,
    }

    try:
        resp = requests.post(url, headers=_headers(), json=payload, timeout=10)
        if not resp.ok:
            st.error("Error al crear el usuario.")
            return None

        data = resp.json()
        if isinstance(data, list) and data:
            return data[0]
        return data

    except Exception as e:
        st.error(f"Error al crear usuario: {e}")
        return None


# -------------------------------------------------
#   ORGANIZATION ↔ USERS
# -------------------------------------------------

def list_users_in_org(org_id: str) -> list[dict]:
    if not org_id:
        return []

    url = f"{SUPABASE_URL}/rest/v1/organization_users"
    params = {
        "select": "user_id, role, role_id, users(*), roles(name), created_at",
        "organization_id": f"eq.{org_id}",
        "order": "created_at.asc",
    }

    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=10)
        if not resp.ok:
            st.error("Error al cargar usuarios de la organización.")
            return []

        data = resp.json()
        return data if isinstance(data, list) else []

    except Exception as e:
        st.error(f"Error al conectar para leer org-users: {e}")
        return []


def add_user_to_org(user_id: str, org_id: str, role_name: str = "viewer") -> dict | None:
    if not user_id or not org_id:
        st.error("Faltan user_id u organization_id.")
        return None

    role_id = _get_role_id_by_name(role_name)
    if not role_id:
        st.error(f"El rol '{role_name}' no existe.")
        return None

    url = f"{SUPABASE_URL}/rest/v1/organization_users"
    payload = {
        "user_id": user_id,
        "organization_id": org_id,
        "role": role_name,
        "role_id": role_id,
    }

    try:
        resp = requests.post(url, headers=_headers(), json=payload, timeout=10)
        if not resp.ok:
            st.error("No se pudo asignar el usuario a la organización.")
            return None

        data = resp.json()
        if isinstance(data, list) and data:
            return data[0]
        return data

    except Exception as e:
        st.error(f"Error al asignar usuario a la organización: {e}")
        return None

