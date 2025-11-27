import bcrypt
from typing import List, Optional
from backend_core.services.supabase_client import supabase


# ---------------------------------------------------------------------
# LOGIN ROBUSTO (case-insensitive)
# ---------------------------------------------------------------------
def login_operator(email: str, password: str):
    """
    Login robusto: insensible a mayúsculas, limpio y seguro.
    """
    try:
        clean_email = email.strip()

        result = (
            supabase.table("ca_operators")
            .select("*")
            .ilike("email", clean_email)
            .execute()
        )

        if not result or not result.data:
            return None

        operator = result.data[0]

        if not operator.get("active", False):
            return None

        stored_hash = operator.get("password_hash")
        if not stored_hash:
            return None

        if isinstance(password, str):
            password = password.encode("utf-8")

        if bcrypt.checkpw(password, stored_hash.encode("utf-8")):
            return operator

        return None

    except Exception as e:
        print("Error en login_operator:", e)
        return None


# ---------------------------------------------------------------------
# OBTENER INFO BÁSICA
# ---------------------------------------------------------------------
def get_operator_info(operator_id: str):
    try:
        result = (
            supabase.table("ca_operators")
            .select("*")
            .eq("id", operator_id)
            .single()
            .execute()
        )
        return result.data
    except Exception:
        return None


# ---------------------------------------------------------------------
# LISTA COMPLETA DE OPERADORES
# ---------------------------------------------------------------------
def list_operators():
    try:
        result = (
            supabase.table("ca_operators")
            .select("*")
            .order("email", desc=False)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


# ---------------------------------------------------------------------
# FILTRO DE PAISES PERMITIDOS
# ---------------------------------------------------------------------
def ensure_country_filter(operator: dict) -> List[str]:
    """
    Devuelve la lista de países permitidos para el operador.
    Si la estructura no existe, retorna una lista vacía.
    """
    if not operator:
        return []

    allowed = operator.get("allowed_countries")
    if isinstance(allowed, list):
        return allowed
    return []


def get_operator_allowed_countries(operator_id: str) -> List[str]:
    op = get_operator_info(operator_id)
    return ensure_country_filter(op)


# ---------------------------------------------------------------------
# SEED GLOBAL DEL OPERADOR
# ---------------------------------------------------------------------
def get_operator_global_seed(operator_id: str) -> Optional[str]:
    try:
        result = (
            supabase.table("ca_operator_seeds")
            .select("*")
            .eq("operator_id", operator_id)
            .single()
            .execute()
        )
        return result.data.get("global_seed") if result and result.data else None
    except Exception:
        return None


def update_operator_global_seed(operator_id: str, seed: str):
    try:
        supabase.table("ca_operator_seeds").upsert(
            {"operator_id": operator_id, "global_seed": seed}
        ).execute()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------
# KYC LOGS
# ---------------------------------------------------------------------
def list_operator_kyc_logs(operator_id: str):
    try:
        result = (
            supabase.table("ca_operator_kyc_logs")
            .select("*")
            .eq("operator_id", operator_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


# ---------------------------------------------------------------------
# UPDATE OPERATOR INFO
# ---------------------------------------------------------------------
def update_operator(operator_id: str, data: dict):
    try:
        supabase.table("ca_operators").update(data).eq("id", operator_id).execute()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------
# CREAR OPERADOR NUEVO
# ---------------------------------------------------------------------
def create_operator(data: dict):
    """
    Crea un nuevo operador en ca_operators.
    Si trae password en texto plano, se hashea automáticamente.
    """
    try:
        new_data = data.copy()

        # Hash automático si viene un password normal
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
