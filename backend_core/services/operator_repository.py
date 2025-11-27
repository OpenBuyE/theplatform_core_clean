"""
Operator Repository — Gestión completa de operadores
Compatible con el panel profesional v3.
"""

import bcrypt
from backend_core.services.supabase_client import supabase


# ---------------------------------------------------------------------
# OBTENER OPERADOR POR EMAIL
# ---------------------------------------------------------------------
def get_operator_by_email(email: str):
    try:
        result = supabase.table("ca_operators").select("*").eq("email", email).execute()
        if result and result.data:
            return result.data[0]
        return None
    except Exception as e:
        print("Error get_operator_by_email:", e)
        return None


# ---------------------------------------------------------------------
# OBTENER OPERADOR POR ID
# ---------------------------------------------------------------------
def get_operator_by_id(operator_id: str):
    try:
        result = supabase.table("ca_operators").select("*").eq("id", operator_id).execute()
        if result and result.data:
            return result.data[0]
        return None
    except Exception as e:
        print("Error get_operator_by_id:", e)
        return None


# ---------------------------------------------------------------------
# LISTAR OPERADORES
# ---------------------------------------------------------------------
def list_operators():
    try:
        result = supabase.table("ca_operators").select("*").order("full_name").execute()
        return result.data if result and result.data else []
    except Exception as e:
        print("Error list_operators:", e)
        return []


# ---------------------------------------------------------------------
# CONTROL DE PAÍSES PERMITIDOS
# ---------------------------------------------------------------------
def ensure_country_filter(operator: dict):
    """
    Devuelve una lista de países permitidos para el operador.
    Si es admin_master → todos.
    """
    if not operator:
        return []

    if operator.get("role") == "admin_master":
        return ["ALL"]

    allowed = operator.get("allowed_countries", [])
    if not isinstance(allowed, list):
        return []

    return allowed


def get_operator_allowed_countries(operator_id: str):
    """
    Devuelve los países que puede gestionar un operador.
    """
    op = get_operator_by_id(operator_id)
    return ensure_country_filter(op)


# ---------------------------------------------------------------------
# SEMILLA GLOBAL DEL OPERADOR (para hashing determinista si aplica)
# ---------------------------------------------------------------------
def get_operator_global_seed(operator_id: str):
    try:
        result = (
            supabase.table("ca_operators")
            .select("global_seed")
            .eq("id", operator_id)
            .execute()
        )
        if result and result.data:
            return result.data[0].get("global_seed")
        return None
    except Exception as e:
        print("Error get_operator_global_seed:", e)
        return None


# ---------------------------------------------------------------------
# ACTUALIZAR OPERADOR
# ---------------------------------------------------------------------
def update_operator(operator_id: str, data: dict):
    try:
        clean = data.copy()

        # Si llega password → hashear
        if "password" in clean and clean["password"]:
            raw = clean["password"].encode("utf-8")
            hashed = bcrypt.hashpw(raw, bcrypt.gensalt()).decode("utf-8")
            clean["password_hash"] = hashed
            del clean["password"]

        result = (
            supabase.table("ca_operators")
            .update(clean)
            .eq("id", operator_id)
            .execute()
        )

        return result.data[0] if result and result.data else None
    except Exception as e:
        print("Error update_operator:", e)
        return None


# ---------------------------------------------------------------------
# CREAR OPERADOR (usado por Admin Operators KYC)
# ---------------------------------------------------------------------
def create_operator(data: dict):
    try:
        new_data = data.copy()

        # Hash automático del password
        if "password" in new_data and new_data["password"]:
            raw = new_data["password"].encode("utf-8")
            hashed = bcrypt.hashpw(raw, bcrypt.gensalt()).decode("utf-8")
            new_data["password_hash"] = hashed
            del new_data["password"]

        # Valores por defecto
        if "active" not in new_data:
            new_data["active"] = True

        if "allowed_countries" not in new_data:
            new_data["allowed_countries"] = []

        result = supabase.table("ca_operators").insert(new_data).execute()

        return result.data[0] if result and result.data else None

    except Exception as e:
        print("Error create_operator:", e)
        return None
