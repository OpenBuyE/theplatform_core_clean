import bcrypt
from typing import List, Optional
from backend_core.services.supabase_client import table


# ============================================================
# HASHING
# ============================================================

def hash_password(password: str) -> str:
    """Hash seguro usando bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# ============================================================
# CRUD PRINCIPAL DE OPERADORES
# ============================================================

def create_operator(
    email: str,
    full_name: str,
    password: str,
    role: str = "operator",
    allowed_countries: Optional[List[str]] = None,
    organization_id: str = "00000000-0000-0000-0000-000000000001",
    active: bool = True,
    global_access: bool = False
):
    """Crea un operador con hashing automático."""
    if allowed_countries is None:
        allowed_countries = []

    operator_data = {
        "email": email,
        "full_name": full_name,
        "role": role,
        "active": active,
        "allowed_countries": allowed_countries,
        "password_hash": hash_password(password),
        "organization_id": organization_id,
        "global_access": global_access,
    }

    return table("ca_operators").insert(operator_data).execute()


def update_operator(operator_id: str, updates: dict):
    """Actualiza campos permitidos de un operador."""
    if "password" in updates:
        updates["password_hash"] = hash_password(updates["password"])
        del updates["password"]

    return (
        table("ca_operators")
        .update(updates)
        .eq("id", operator_id)
        .execute()
    )


def delete_operator(operator_id: str):
    """Desactiva operador (soft delete)."""
    return (
        table("ca_operators")
        .update({"active": False})
        .eq("id", operator_id)
        .execute()
    )


def list_operators():
    """Listado completo para panel Admin/KYC."""
    return table("ca_operators").select("*").execute()


def get_operator_info(operator_id: str):
    """Obtiene datos completos de un operador."""
    result = (
        table("ca_operators")
        .select("*")
        .eq("id", operator_id)
        .execute()
    )
    return result[0] if result else None


# ============================================================
# LOGIN: BÚSQUEDA POR EMAIL
# ============================================================

def find_by_email(email: str):
    result = (
        table("ca_operators")
        .select("*")
        .eq("email", email)
        .eq("active", True)
        .execute()
    )
    return result[0] if result else None


# ============================================================
# SEGURIDAD MULTI-PAÍS
# ============================================================

def ensure_country_filter(operator: dict, target_country: str) -> bool:
    """
    Seguridad estricta:
    - Admin Master y God → acceso total
    - Otros operadores → acceso solo si el país está permitido
    """
    if operator.get("role") in ("admin_master", "god"):
        return True

    allowed = operator.get("allowed_countries", [])
    return target_country in allowed


# ============================================================
# KYC LOGS (para Admin Operators KYC)
# ============================================================

def add_operator_kyc_log(operator_id: str, action: str, notes: str = ""):
    """Inserta un registro KYC para un operador."""
    entry = {
        "operator_id": operator_id,
        "action": action,
        "notes": notes,
    }
    return table("ca_operator_kyc_logs").insert(entry).execute()


def list_operator_kyc_logs(operator_id: str):
    """Lista todos los logs KYC de un operador."""
    return (
        table("ca_operator_kyc_logs")
        .select("*")
        .eq("operator_id", operator_id)
        .order("created_at", desc=True)
        .execute()
    )


# ============================================================
# AUTO-CREACIÓN DEL GLOBAL ADMIN
# ============================================================

def create_builtin_global_admin():
    """
    Crea automáticamente el GlobalAdmin si NO existe.
    Nunca reemplaza, nunca duplica.
    """
    try:
        existing = (
            table("ca_operators")
            .select("id")
            .eq("email", "GlobalAdmin")
            .execute()
        )
        if existing:
            return  # ya existe

        admin_data = {
            "email": "GlobalAdmin",
            "full_name": "Administrador Global",
            "role": "admin_master",
            "active": True,
            "allowed_countries": ["ES", "PT", "FR", "IT", "DE"],
            "password_hash": hash_password("101010"),
            "organization_id": "00000000-0000-0000-0000-000000000001",
            "global_access": True,
        }

        table("ca_operators").insert(admin_data).execute()

    except Exception:
        pass  # silencioso por seguridad


# ============================================================
# EJECUCIÓN AUTOMÁTICA AL IMPORTAR EL MÓDULO
# ============================================================
create_builtin_global_admin()
