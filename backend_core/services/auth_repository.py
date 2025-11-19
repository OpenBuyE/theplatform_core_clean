import hashlib
import requests
import streamlit as st

SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = st.secrets["SUPABASE_SERVICE_ROLE"]

# Secreto para saltear hashes. En producción, configura AUTH_SECRET en st.secrets.
AUTH_SECRET = st.secrets.get("AUTH_SECRET", "CHANGE_ME_IN_PRODUCTION")


def _headers() -> dict:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _hash_password(password: str) -> str:
    """
    Hash simple con SHA256 + secreto.
    Para producción se recomienda usar bcrypt/argon2,
    pero esto mantiene el sistema funcionando sin nuevas dependencias.
    """
    base = f"{AUTH_SECRET}:{password}".encode("utf-8")
    return hashlib.sha256(base).hexdigest()


# -------------------------------------------------
#   HELPERS SOBRE TABLA users
# -------------------------------------------------

def _get_user_by_email(email: str) -> dict | None:
    """
    Busca un usuario en la tabla public.users por email.
    """
    url = f"{SUPABASE_URL}/rest/v1/users"
    params = {
        "select": "*",
        "email": f"eq.{email}",
    }

    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=10)
        if not resp.ok:
            st.error(f"[AUTH] Error buscando usuario ({resp.status_code}).")
            return None

        data = resp.json()
        if isinstance(data, list) and data:
            return data[0]
        return None

    except Exception as e:
        st.error(f"[AUTH] Error al conectar para leer usuarios: {e}")
        return None


def _create_user(name: str, email: str) -> dict | None:
    """
    Crea un usuario en public.users.
    """
    url = f"{SUPABASE_URL}/rest/v1/users"
    payload = {
        "name": name,
        "email": email,
    }

    try:
        resp = requests.post(url, headers=_headers(), json=payload, timeout=10)
        if not resp.ok:
            st.error(f"[AUTH] Error al crear usuario ({resp.status_code}).")
            # st.write(resp.text)
            return None

        data = resp.json()
        if isinstance(data, list) and data:
            return data[0]
        return data

    except Exception as e:
        st.error(f"[AUTH] Error al crear usuario: {e}")
        return None


# -------------------------------------------------
#   AUTH_USERS (credenciales)
# -------------------------------------------------

def register_user_with_password(name: str, email: str, password: str) -> dict | None:
    """
    Crea un usuario de aplicación con credenciales:
    - Crea (o reutiliza) usuario en public.users
    - Crea entrada en public.auth_users con password_hash
    """
    # 1) Asegurar usuario en tabla users
    user = _get_user_by_email(email)
    if not user:
        user = _create_user(name, email)

    if not user:
        st.error("[AUTH] No se pudo crear/obtener el usuario.")
        return None

    user_id = user["id"]

    # 2) Hash de contraseña
    password_hash = _hash_password(password)

    # 3) Insertar en auth_users
    url = f"{SUPABASE_URL}/rest/v1/auth_users"
    payload = {
        "user_id": user_id,
        "email": email,
        "password_hash": password_hash,
    }

    try:
        resp = requests.post(url, headers=_headers(), json=payload, timeout=10)

        if not resp.ok:
            st.error(f"[AUTH] Error al crear credenciales ({resp.status_code}).")
            # st.write(resp.text)
            return None

        data = resp.json()
        if isinstance(data, list) and data:
            return data[0]
        return data

    except Exception as e:
        st.error(f"[AUTH] Error al registrar credenciales: {e}")
        return None


def authenticate_user(email: str, password: str) -> dict | None:
    """
    Verifica email + password contra auth_users.
    Devuelve un dict con user_id y email si es válido, o None si falla.
    """
    url = f"{SUPABASE_URL}/rest/v1/auth_users"
    params = {
        "select": "user_id, email, password_hash",
        "email": f"eq.{email}",
    }

    try:
        resp = requests.get(url, headers=_headers(), params=params, timeout=10)
        if not resp.ok:
            st.error(f"[AUTH] Error al autenticar ({resp.status_code}).")
            return None

        data = resp.json()
        if not data:
            return None

        record = data[0]
        expected_hash = record["password_hash"]
        given_hash = _hash_password(password)

        if given_hash != expected_hash:
            return None

        return {
            "user_id": record["user_id"],
            "email": record["email"],
        }

    except Exception as e:
        st.error(f"[AUTH] Error al autenticar usuario: {e}")
        return None
