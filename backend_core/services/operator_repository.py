# backend_core/services/operator_repository.py

from backend_core.services.supabase_client import table


# ===============================================================
# 📌 LISTAR OPERADORES
# ===============================================================

def list_operators():
    return (
        table("ca_operators")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )


# ===============================================================
# 📌 OBTENER OPERADOR POR ID
# ===============================================================

def get_operator(operator_id: str):
    return (
        table("ca_operators")
        .select("*")
        .eq("id", operator_id)
        .single()
        .execute()
    )


# ===============================================================
# 📌 OBTENER INFO BÁSICA PARA DASHBOARD
# ===============================================================

def get_operator_info(operator_id: str):
    return (
        table("ca_operators")
        .select("id, email, role, allowed_countries, global_access, organization_id")
        .eq("id", operator_id)
        .single()
        .execute()
    )


# ===============================================================
# 📌 COUNTRIES — ROLES Y PERMISOS
# ===============================================================

def get_operator_allowed_countries(operator_id: str):
    op = get_operator(operator_id)
    if not op:
        return []
    return op.get("allowed_countries", [])


def ensure_country_filter(operator_id: str, country: str) -> bool:
    """
    Devuelve True si el operador TIENE permiso sobre country.
    """
    op = get_operator(operator_id)
    if not op:
        return False

    if op.get("global_access"):
        return True

    allowed = op.get("allowed_countries") or []
    return country in allowed


# ===============================================================
# 📌 CREAR OPERADOR
# ===============================================================

def create_operator(data: dict):
    return table("ca_operators").insert(data).execute()


# ===============================================================
# 📌 ACTUALIZAR OPERADOR
# ===============================================================

def update_operator(operator_id: str, data: dict):
    return (
        table("ca_operators")
        .update(data)
        .eq("id", operator_id)
        .execute()
    )


# ===============================================================
# 📌 BORRAR OPERADOR (desactivar)
# ===============================================================

def disable_operator(operator_id: str):
    return (
        table("ca_operators")
        .update({"active": False})
        .eq("id", operator_id)
        .execute()
    )


# ===============================================================
# 📌 KYC LOGS
# ===============================================================

def list_operator_kyc_logs(operator_id: str):
    return (
        table("ca_operator_kyc")
        .select("*")
        .eq("operator_id", operator_id)
        .order("created_at", desc=True)
        .execute()
    )


# ===============================================================
# 📌 GLOBAL SEED (para Engine Monitor)
# ===============================================================

def get_operator_global_seed(operator_id: str):
    return (
        table("ca_operator_seeds")
        .select("*")
        .eq("operator_id", operator_id)
        .single()
        .execute()
    )
