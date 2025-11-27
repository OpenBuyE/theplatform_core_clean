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
# MODERN KPI FUNCTIONS (usadas por la arquitectura actual)
# ==========================================================================
def sessions_active(operator_id: str, country: str):
    c = ensure_country_filter(operator_id, country)
    if not c:
        return 0

    q = (
        table("ca_sessions")
        .select("id")
        .eq("country", c)
        .eq("status", "active")
    )
    return _count(q)


def sessions_parked(operator_id: str, country: str):
    c = ensure_country_filter(operator_id, country)
    if not c:
        return 0

    q = (
        table("ca_sessions")
        .select("id")
        .eq("country", c)
        .eq("status", "parked")
    )
    return _count(q)


def sessions_finished(operator_id: str, country: str):
    c = ensure_country_filter(operator_id, country)
    if not c:
        return 0

    q = (
        table("ca_sessions")
        .select("id")
        .eq("country", c)
        .eq("status", "finished")
    )
    return _count(q)


def sessions_expired(operator_id: str, country: str):
    c = ensure_country_filter(operator_id, country)
    if not c:
        return 0

    q = (
        table("ca_sessions")
        .select("id")
        .eq("country", c)
        .eq("status", "expired")
    )
    return _count(q)


def get_kpi_wallets_total(operator_id: str, country: str):
    """
    Placeholder profesional para evitar fallos de importación.
    """
    c = ensure_country_filter(operator_id, country)
    if not c:
        return 0
    return 0


def get_kpi_wallets_pending(operator_id: str, country: str):
    c = ensure_country_filter(operator_id, country)
    if not c:
        return 0
    return 0


# ==========================================================================
# LEGACY WRAPPERS — Para compatibilidad con vistas antiguas
# ==========================================================================
def get_kpi_sessions_active(operator_id: str, country: str):
    """
    Wrapper para compatibilidad con versiones antiguas del dashboard.
    """
    return sessions_active(operator_id, country)


def get_kpi_sessions_parked(operator_id: str, country: str):
    return sessions_parked(operator_id, country)


def get_kpi_sessions_finished(operator_id: str, country: str):
    return sessions_finished(operator_id, country)


def get_kpi_sessions_expired(operator_id: str, country: str):
    return sessions_expired(operator_id, country)


def wallet_deposit_ok(operator_id: str, country: str):
    """
    Wrapper legacy.
    """
    return get_kpi_wallets_total(operator_id, country)
