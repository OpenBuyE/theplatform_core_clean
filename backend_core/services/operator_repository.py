"""
Operator Repository — Gestión completa de operadores
Versión Final y 100% compatible con el panel profesional.
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
# INFO COMPLETA DEL OPERADOR (solicitado por el panel)
# ---------------------------------------------------------------------
def get_operator_info(operator_id: str):
    """
    Devuelve todos los campos del operador, usado en Dashboard.
    """
    return get_operator_by_id(operator_id)


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
# LISTAR KYC LOGS (solicitado por Admin Operators KYC)
# ---------------------------------------------------------------------
def list_operator_kyc_logs(operator_id: str):
    """
    Devuelve logs de validaciones KYC del operador.
    La tabla se llama ca_operator_kyc_logs (crear en supabase si no existe).
    """
    try:
        result = (
            supabase.table("ca_operator_kyc_logs")
            .select("*")
            .eq("operator_id", operator_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data if result and result.data else []
    except Exception as e:
        print("Error list_operator_kyc_logs:", e)
        return []


# ---------------------------------------------------------------------
# CONTROL DE PAÍSES PERMITIDOS
# ---------------------------------------------------------------------
def ensure_country_filter(operator: dict):
    if not operator:
        return []

    if operator.get("role") == "admin_master":
        return ["ALL"]

    allowed = operator.get("allowed_countries", [])
    if not isinstance(allowed, list):
        return []

    return allowed


def get_operator_allowed_countries(operator_id: str):
    op = get_operator_by_id(operator_id)
    return ensure_country_filter(op)


# ---------------------------------------------------------------------
# SEMILLA GLOBAL (opcional para motor determinista)
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
# CREAR OPERADOR
# ---------------------------------------------------------------------
def create_operator(data: dict):
    try:
        new_data = data.copy()

        if "password" in new_data and new_data["password"]:
            raw = new_data["password"].encode("utf-8")
            hashed = bcrypt.hashpw(raw, bcrypt.gensalt()).decode("utf-8")
            new_data["password_hash"] = hashed
            del new_data["password"]

        if "active" not in new_data:
            new_data["active"] = True

        if "allowed_countries" not in new_data:
            new_data["allowed_countries"] = []

        result = supabase.table("ca_operators").insert(new_data).execute()

        return result.data[0] if result and result.data else None

    except Exception as e:
        print("Error create_operator:", e)
        return None
