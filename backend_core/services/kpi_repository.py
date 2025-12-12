# backend_core/services/kpi_repository.py

from backend_core.services.supabase_client import table
from backend_core.services.operator_repository import (
    ensure_country_filter,
    get_operator,
)

# ==========================================================================
# Helpers
# ==========================================================================

def _count(query):
    """
    Ejecuta una query Supabase y devuelve el número de filas.
    Compatible con Supabase v2 (APIResponse).
    """
    try:
        res = query.execute()
        if hasattr(res, "data") and res.data is not None:
            return len(res.data)
        return 0
    except Exception:
        return 0


def _resolve_countries(operator_id: str, country: str | None):
    """
    Determina los países válidos para un operador.
    - Si se pasa country: valida permisos
    - Si NO se pasa country: usa allowed_countries del operador
    """
    # Caso 1: country explícito
    if country:
        allowed = ensure_country_filter(operator_id, country)
        return [allowed] if allowed else []

    # Caso 2: todos los países permitidos
    resp = get_operator(operator_id)
    op = resp.data if resp else None

    if not op:
        return []

    if op.get("global_access"):
        return op.get("allowed_countries", []) or []

    return op.get("allowed_countries", []) or []


# ==========================================================================
# KPI CORE FUNCTIONS
# ==========================================================================

def _sessions_by_status(operator_id: str, status: str, country: str | None = None):
    total = 0
    for c in _resolve_countries(operator_id, country):
        total += _count(
            table("ca_sessions")
            .select("id")
            .eq("country", c)
            .eq("status", status)
        )
    return total


def _simple_count(table_name: str, operator_id: str, country: str | None = None):
    total = 0
    for c in _resolve_countries(operator_id, country):
        total += _count(
            table(table_name)
            .select("id")
            .eq("country", c)
        )
    return total


# ==========================================================================
# PUBLIC KPI FUNCTIONS (MODERN)
# ==========================================================================

def sessions_active(operator_id: str, country: str | None = None):
    return _sessions_by_status(operator_id, "active", country)


def sessions_parked(operator_id: str, country: str | None = None):
    return _sessions_by_status(operator_id, "parked", country)


def sessions_finished(operator_id: str, country: str | None = None):
    return _sessions_by_status(operator_id, "finished", country)


def sessions_expired(operator_id: str, country: str | None = None):
    return _sessions_by_status(operator_id, "expired", country)


def providers_total(operator_id: str, country: str | None = None):
    return _simple_count("providers_v2", operator_id, country)


def products_total(operator_id: str, country: str | None = None):
    return _simple_count("products_v2", operator_id, country)


def categories_total(operator_id: str, country: str | None = None):
    return _simple_count("categories_v2", operator_id, country)


def wallets_total(operator_id: str, country: str | None = None):
    # Aún no implementado
    return 0


# ==========================================================================
# LEGACY WRAPPERS (COMPATIBILIDAD TOTAL CON DASHBOARDS)
# ==========================================================================

def get_kpi_sessions_active(o, c=None): return sessions_active(o, c)
def get_kpi_sessions_parked(o, c=None): return sessions_parked(o, c)
def get_kpi_sessions_finished(o, c=None): return sessions_finished(o, c)
def get_kpi_sessions_expired(o, c=None): return sessions_expired(o, c)

def get_kpi_providers_total(o, c=None): return providers_total(o, c)
def get_kpi_products_total(o, c=None): return products_total(o, c)
def get_kpi_categories_total(o, c=None): return categories_total(o, c)

def get_kpi_wallets_total(o, c=None): return wallets_total(o, c)

# Alias antiguos usados por vistas legacy
def wallet_deposit_ok(o, c=None): return wallets_total(o, c)
