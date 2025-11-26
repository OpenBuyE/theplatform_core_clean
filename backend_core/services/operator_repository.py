import typing as t
from backend_core.services.supabase_client import table

# =========================================================
# MODELO DE ROLES (CONSTANTES)
# =========================================================

ROLE_EXTERNAL_AUDITOR = "external_auditor"
ROLE_VIEWER = "viewer"
ROLE_OPERATOR_BASIC = "operator_basic"
ROLE_OPERATOR_PRO = "operator_pro"
ROLE_ADMIN_MASTER = "admin_master"
ROLE_SYSTEM_ROOT = "system_root"

GLOBAL_ACCESS_ROLES = {ROLE_ADMIN_MASTER, ROLE_SYSTEM_ROOT}


# =========================================================
# OPERATORS — HELPERS BÁSICOS
# =========================================================

def get_operator_by_id(operator_id: str) -> t.Optional[dict]:
    """
    Devuelve el operador desde ca_operators.
    """
    resp = (
        table("ca_operators")
        .select("*")
        .eq("id", operator_id)
        .single()
        .execute()
    )
    return resp.data if hasattr(resp, "data") else resp.get("data")


def operator_has_global_access(operator: dict) -> bool:
    """
    Devuelve True si el operador tiene acceso global (rol o flag).
    """
    if not operator:
        return False

    role = operator.get("role")
    if role in GLOBAL_ACCESS_ROLES:
        return True

    if operator.get("global_access") is True:
        return True

    return False


def get_operator_allowed_countries(operator_id: str) -> t.Optional[t.List[str]]:
    """
    Devuelve lista de países permitidos para el operador.
    Si tiene acceso global → devuelve None (interpretado como "sin filtro").
    """
    operator = get_operator_by_id(operator_id)
    if not operator:
        return []

    if operator_has_global_access(operator):
        # None = sin filtro de país
        return None

    resp = (
        table("ca_operator_regions")
        .select("country_code")
        .eq("operator_id", operator_id)
        .execute()
    )

    rows = resp.data if hasattr(resp, "data") else resp.get("data") or []

    countries = sorted({row["country_code"] for row in rows if "country_code" in row})

    return countries


def ensure_country_filter(query_builder, allowed_countries: t.Optional[t.List[str]]):
    """
    Helper genérico para aplicar filtro de país en una QueryBuilder de supabase_client.

    - Si allowed_countries es None → no se aplica filtro (Admin Master / Root).
    - Si lista vacía → no devuelve nada.
    - Si tiene valores → aplica un IN("country_code", lista).
    """
    if allowed_countries is None:
        # acceso global → no filtrar por país
        return query_builder

    if not allowed_countries:
        # operador sin países asignados → devolver resultado vacío
        # truco: filtrar por country_code inexistente
        return query_builder.eq("country_code", "__NO_COUNTRY__")

    # Supabase REST: usar in_ si tu wrapper lo soporta
    return query_builder.in_("country_code", allowed_countries)
