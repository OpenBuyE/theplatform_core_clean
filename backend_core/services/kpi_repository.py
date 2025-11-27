# backend_core/services/kpi_repository.py

from backend_core.services.supabase_client import table
from backend_core.services.operator_repository import ensure_country_filter


# ==========================================================================
# Helpers
# ==========================================================================
def _count(q):
    try:
        res = q.execute()
        if isinstance(res, list):
            return len(res)
        if isinstance(res, dict) and res.get("data"):
            return len(res["data"])
        return 0
    except Exception:
        return 0


# ==========================================================================
# MODERN KPI FUNCTIONS
# ==========================================================================
def sessions_active(operator_id: str, country: str):
    c = ensure_country_filter(operator_id, country)
    if not c: return 0
    return _count(table("ca_sessions").select("id").eq("country", c).eq("status", "active"))


def sessions_parked(operator_id: str, country: str):
    c = ensure_country_filter(operator_id, country)
    if not c: return 0
    return _count(table("ca_sessions").select("id").eq("country", c).eq("status", "parked"))


def sessions_finished(operator_id: str, country: str):
    c = ensure_country_filter(operator_id, country)
    if not c: return 0
    return _count(table("ca_sessions").select("id").eq("country", c).eq("status", "finished"))


def sessions_expired(operator_id: str, country: str):
    c = ensure_country_filter(operator_id, country)
    if not c: return 0
    return _count(table("ca_sessions").select("id").eq("country", c).eq("status", "expired"))


def providers_total(operator_id: str, country: str):
    c = ensure_country_filter(operator_id, country)
    if not c: return 0
    return _count(table("providers_v2").select("id").eq("country", c))


def products_total(operator_id: str, country: str):
    c = ensure_country_filter(operator_id, country)
    if not c: return 0
    return _count(table("products_v2").select("id").eq("country", c))


def categories_total(operator_id: str, country: str):
    c = ensure_country_filter(operator_id, country)
    if not c: return 0
    # categorías están en categories_v2
    return _count(table("categories_v2").select("id").eq("country", c))


def wallets_total(operator_id: str, country: str):
    return 0  # AÚN NO IMPLEMENTADO


# ==========================================================================
# LEGACY WRAPPERS (COMPATIBILIDAD TOTAL)
# ==========================================================================
def get_kpi_sessions_active(o, c): return sessions_active(o, c)
def get_kpi_sessions_parked(o, c): return sessions_parked(o, c)
def get_kpi_sessions_finished(o, c): return sessions_finished(o, c)
def get_kpi_sessions_expired(o, c): return sessions_expired(o, c)

def get_kpi_providers_total(o, c): return providers_total(o, c)
def get_kpi_products_total(o, c): return products_total(o, c)
def get_kpi_categories_total(o, c): return categories_total(o, c)

def get_kpi_wallets_total(o, c): return wallets_total(o, c)

# Alias antiguos usados por Operator Dashboard Pro
def wallet_deposit_ok(o, c): return wallets_total(o, c)
