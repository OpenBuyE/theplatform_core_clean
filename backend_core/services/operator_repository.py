import bcrypt
from backend_core.services.db import supabase

# ============================================================
#  OPERATORS REPOSITORY (VERSIÓN ESTABLE Y COMPATIBLE)
# ============================================================

def list_operators():
    """Devuelve todos los operadores."""
    result = supabase.table("operators").select("*").execute()
    return result.data if result.data else []


def get_operator_by_email(email: str):
    """Obtiene un operador por su email (GlobalAdmin o normal)."""
    result = supabase.table("operators").select("*").eq("email", email).limit(1).execute()
    if result.data:
        return result.data[0]
    return None


def get_operator_by_id(operator_id: str):
    """Obtiene un operador por ID."""
    result = supabase.table("operators").select("*").eq("id", operator_id).limit(1).execute()
    if result.data:
        return result.data[0]
    return None


def create_operator(email: str, password: str, role: str = "operator"):
    """Crea un nuevo operador."""
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    data = {
        "email": email,
        "password_hash": password_hash,
        "role": role,
        "active": True,
        "allowed_countries": ["ES"]
    }
    supabase.table("operators").insert(data).execute()
    return True


def verify_operator_credentials(email: str, password: str):
    """Verifica credenciales del login."""
    operator = get_operator_by_email(email)
    if not operator:
        return None

    if not operator.get("active", False):
        return None

    stored_hash = operator.get("password_hash")
    if not stored_hash:
        return None

    try:
        if bcrypt.checkpw(password.encode(), stored_hash.encode()):
            return operator
        return None
    except Exception:
        return None


def list_operator_kyc_logs(operator_id: str):
    """Devuelve los logs KYC del operador."""
    result = (
        supabase.table("operator_kyc_logs")
        .select("*")
        .eq("operator_id", operator_id)
        .execute()
    )
    return result.data if result.data else []


# ============================================================
#  COMPATIBILIDAD CON EL DASHBOARD
# ============================================================

def get_operator_info(operator_id: str):
    """Devuelve la información necesaria para las vistas del dashboard."""
    return get_operator_by_id(operator_id)


def ensure_country_filter(operator):
    """Devuelve lista de países permitidos para filtrar productos y sesiones."""
    if not operator:
        return ["ES"]
    return operator.get("allowed_countries", ["ES"])


def get_operator_global_seed(operator_id: str):
    """Devuelve la semilla global del operador."""
    result = (
        supabase.table("operator_seeds")
        .select("*")
        .eq("operator_id", operator_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None
