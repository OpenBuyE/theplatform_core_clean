# backend_core/services/operator_repository.py

from backend_core.services.supabase_client import table


# =========================================================
# HELPERS
# =========================================================
def _fetch_one(query):
    try:
        result = query.execute()
        return result[0] if result else None
    except:
        return None


def _fetch_many(query):
    try:
        result = query.execute()
        return result if result else []
    except:
        return []


# =========================================================
# LISTADO DE OPERADORES
# =========================================================
def list_operators(active_only=True, country=None):
    q = table("ca_operators").select("*")

    if active_only:
        q = q.eq("active", True)

    if country:
        q = q.eq("country", country)

    return _fetch_many(q)


# =========================================================
# INFO DE OPERADOR
# =========================================================
def get_operator(operator_id: str):
    q = (
        table("ca_operators")
        .select("*")
        .eq("id", operator_id)
        .single()
    )
    return _fetch_one(q)


def get_operator_info(operator_id: str):
    return get_operator(operator_id)


# =========================================================
# CAMPOS REQUERIDOS POR VARIAS VISTAS
# =========================================================
def get_operator_allowed_countries(operator_id: str):
    op = get_operator(operator_id)
    if not op:
        return []
    return op.get("allowed_countries", [])


def get_operator_role(operator_id: str):
    op = get_operator(operator_id)
    if not op:
        return None
    return op.get("role")


def get_operator_country(operator_id: str):
    op = get_operator(operator_id)
    if not op:
        return None
    return op.get("country")


# =========================================================
# CREAR OPERADOR
# =========================================================
def create_operator(
    email: str,
    full_name: str,
    role: str,
    password_hash: str,
    allowed_countries: list,
    organization_id: str,
    active: bool = True,
    global_access: bool = False,
):
    data = {
        "email": email,
        "full_name": full_name,
        "role": role,
        "password_hash": password_hash,
        "allowed_countries": allowed_countries,
        "organization_id": organization_id,
        "active": active,
        "global_access": global_access,
    }

    q = table("ca_operators").insert(data)
    try:
        res = q.execute()
        return res[0] if res else None
    except Exception:
        return None


# =========================================================
# ACTUALIZAR OPERADOR
# =========================================================
def update_operator(operator_id: str, data: dict):
    q = (
        table("ca_operators")
        .update(data)
        .eq("id", operator_id)
    )
    try:
        res = q.execute()
        return res[0] if res else None
    except Exception:
        return None


# =========================================================
# DESACTIVAR OPERADOR
# =========================================================
def disable_operator(operator_id: str):
    return update_operator(operator_id, {"active": False})


# =========================================================
# FILTROS
# =========================================================
def list_operators_by_role(role: str):
    q = table("ca_operators").select("*").eq("role", role)
    return _fetch_many(q)


def list_operators_by_country(country: str):
    q = table("ca_operators").select("*").eq("country", country)
    return _fetch_many(q)


def search_operators(text: str):
    q = (
        table("ca_operators")
        .select("*")
        .ilike("full_name", f"%{text}%")
    )
    return _fetch_many(q)


# =========================================================
# KYC LOGS (placeholder)
# =========================================================
def list_operator_kyc_logs(operator_id: str):
    """
    Placeholder — evita errores mientras se crea el módulo real.
    """
    return []
