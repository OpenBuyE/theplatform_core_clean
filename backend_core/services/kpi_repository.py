# backend_core/services/kpi_repository.py

from backend_core.services.supabase_client import table
from backend_core.services.operator_repository import ensure_country_filter


# ==========================================================================
# HELPERS
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
# MODERN KPI FUNCTIONS (nueva arquitectura)
# ==========================================================================
def sessions_active(operator_id: str, country: str):
    c = ensure_country_filter(operator_id, country)
    if not c:
        return 0
    return _count(
        table("ca_sessions")
        .select("id")
        .eq("country", c)
        .eq("status", "active")
    )


def sessions_parked(operator_id: str, country: str):
    c = ensure_country_filter(operator_id, country)
    if not c:
        return 0
    return _count(
        table("ca_sessions")
        .select("id")
        .eq("country", c)
        .eq("status", "parked")
    )


def sessions_finished(operator_id: str, country: str):
    c = ensure_country_filter(operator_id, country)
    if not c:
        return 0
    return _count(
        table("ca_sessions")
        .select("id")
        .eq("country", c)
        .eq("status", "finished")
    )


def sessions_expired(operator_id: str, country: str):
    c = ensure_country_filter(operator_id, country)
    if not c:
        return 0
    return _count(
        table("ca_sessions")
        .select("id")
        .eq("country", c)
        .eq("status", "expired")
    )


def providers_total(operator_id: str, country: str):
    c = ensure_country_filter(operator_id, country)
    if not c:
        return 0
    return _count(
        table("providers_v2")
        .select("id")
        .eq("country", c)
    )


def wallets_total(operator_id: str, country: str):
    """
    Placeholder — no existe tabla wallets implementada todavía.
    """
    return 0


# ==========================================================================
# LEGACY WRAPPERS — compatibilidad total con vistas antiguas
# ==========================================================================
def get_kpi_sessions_active(operator_id: str, country: str):
    return sessions_active(operator_id, country)


def get_kpi_sessions_parked(operator_id: str, country: str):
    return sessions_parked(operator_id, country)


def get_kpi_sessions_finished(operator_id: str, country: str):
    return sessions_finished(operator_id, country)


def get_kpi_sessions_expired(operator_id: str, country: str):
    return sessions_expired(operator_id, country)


def get_kpi_wallets_total(operator_id: str, country: str):
    return wallets_total(operator_id, country)


def get_kpi_wallets_pending(operator_id: str, country: str):
    return 0


def wallet_deposit_ok(operator_id: str, country: str):
    return wallets_total(operator_id, country)


def get_kpi_providers_total(operator_id: str, country: str):
    return providers_total(operator_id, country)
