import streamlit as st
import requests

SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = st.secrets["SUPABASE_SERVICE_ROLE"]


def _headers() -> dict:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def get_user_permissions(user_id: str, org_id: str) -> set[str]:
    """
    Devuelve el conjunto de permisos asignados a un usuario
    para una organización concreta.

    Usa la tabla organization_users y hace join con roles → role_permissions → permissions.
    """

    if not user_id or not org_id:
        return set()

    url = f"{SUPABASE_URL}/rest/v1/organization_users"

    params = {
        "select": "role_id, roles(id, name, role_permissions(permissions(code)))",
        "user_id": f"eq.{user_id}",
        "organization_id": f"eq.{org_id}",
    }

    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=10)

        if not resp.ok:
            st.error(f"Error al cargar permisos del usuario ({resp.status_code}).")
            # st.write(resp.text)
            return set()

        data = resp.json()
        if not data:
            return set()

        # Primer registro (user_id + org_id es único)
        role_block = data[0].get("roles")
        if not role_block:
            return set()

        # Extraer permisos
        perms = set()

        for rp in role_block.get("role_permissions", []):
            perm = rp["permissions"]["code"]
            perms.add(perm)

        return perms

    except Exception as e:
        st.error(f"Error al leer permisos: {e}")
        return set()
