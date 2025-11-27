# backend_core/services/operator_repository.py

import uuid
from backend_core.services.supabase_client import table


# =========================================================
# HELPERS
# =========================================================

def _fetch_one(q):
    """
    Ejecuta una query y devuelve un único registro o None.
    """
    try:
        res = q.execute()
        if isinstance(res, list) and res:
            return res[0]
        elif isinstance(res, dict) and res.get("data"):
            return res["data"][0]
        return None
    except Exception:
        return None


def _fetch_many(q):
    """
    Ejecuta una query y devuelve lista (vacía si falla).
    """
    try:
        res = q.execute()
        if isinstance(res, list):
            return res
        elif isinstance(res, dict) and res.get("data"):
            return res["data"]
        return []
    except Exception:
        return []


# =========================================================
# GETTERS PRINCIPALES
# =========================================================

def get_operator(operator_id: str):
    q = (
        table("ca_operators")
        .select("*")
        .eq("id", operator_id)
        .limit(1)
    )
    return _fetch_one(q)


def get_operator_by_email(email: str):
    q = (
        table("ca_operators")
        .select("*")
        .eq("email", email)
        .limit(1)
    )
    return _fetch_one(q)


def list_operators():
    q = table("ca_operators").select("*").order("created_at", desc=True)
    return _fetch_many(q)


# =========================================================
# ROLES Y PAÍSES
# =========================================================

def get_operator_allowed_countries(operator_id: str):
    op = get_operator(operator_id)
    if not op:
        return []
    return op.get("allowed_countries", []) or []


def ensure_country_filter(operator_id: str, country: str):
    """
    Devuelve el país si el operador tiene permiso.
    Devuelve None si NO tiene permiso.
    """
    op = get_operator(operator_id)
    if not op:
        return None

    allowed = op.get("allowed_countries", []) or []

    # Admin global puede entrar a todo
    if op.get("global_access", False):
        return country

    if country in allowed:
        return country

    return None


def get_operator_info(operator_id: str):
    """
    Información básica, solicitado desde Operator Dashboard.
    """
    op = get_operator(operator_id)
    if not op:
        return None

    return {
        "id": op["id"],
        "email": op.get("email"),
        "full_name": op.get("full_name"),
        "role": op.get("role", "operator"),
        "allowed_countries": op.get("allowed_countries", []),
        "global_access": op.get("global_access", False),
        "organization_id": op.get("organization_id"),
        "active": op.get("active", True),
    }


# =========================================================
# CRUD COMPLETO
# =========================================================

def create_operator(
    email: str,
    password_hash: str,
    full_name: str,
    role: str,
    allowed_countries: list,
    global_access: bool,
    organization_id: str,
    active: bool = True
):
    new_id = str(uuid.uuid4())

    data = {
        "id": new_id,
        "email": email,
        "password_hash": password_hash,
        "full_name": full_name,
        "role": role,
        "allowed_countries": allowed_countries,
        "global_access": global_access,
        "organization_id": organization_id,
        "active": active,
    }

    q = table("ca_operators").insert(data)
    try:
        q.execute()
        return new_id
    except Exception:
        return None


def update_operator(operator_id: str, data: dict):
    if not data:
        return False

    q = (
        table("ca_operators")
        .update(data)
        .eq("id", operator_id)
    )
    try:
        q.execute()
        return True
    except Exception:
        return False


def delete_operator(operator_id: str):
    q = table("ca_operators").delete().eq("id", operator_id)
    try:
        q.execute()
        return True
    except Exception:
        return False


# =========================================================
# OPERADORES + KYC LOGS
# =========================================================

def list_operator_kyc_logs(operator_id: str):
    q = (
        table("ca_operator_kyc")
        .select("*")
        .eq("operator_id", operator_id)
        .order("created_at", desc=True)
    )
    return _fetch_many(q)


# =========================================================
# AUTH HELPERS
# =========================================================

def validate_email_exists(email: str):
    return True if get_operator_by_email(email) else False


def authenticate(email: str, password_hash: str):
    """
    Devuelve operador si coincide email + password_hash (ya validado en login.py)
    """
    op = get_operator_by_email(email)
    if not op:
        return None

    if op.get("password_hash") == password_hash:
        return op

    return None


# =========================================================
# LISTA PARA ADMIN MANAGER PRO
# =========================================================

def list_operators_minimal():
    """
    Versión ligera para listas en Operator Manager Pro.
    """
    q = (
        table("ca_operators")
        .select("id,email,full_name,role,active")
        .order("created_at", desc=True)
    )
    return _fetch_many(q)


# =========================================================
# TOOLS PARA DASHBOARD Y VISTAS
# =========================================================

def get_operator_role(operator_id):
    op = get_operator(operator_id)
    if not op:
        return None
    return op.get("role", "operator")


def operator_is_admin(operator_id):
    role = get_operator_role(operator_id)
    return role in ["admin_master", "god"]


def operator_is_global(operator_id):
    op = get_operator(operator_id)
    if not op:
        return False
    return bool(op.get("global_access", False))
