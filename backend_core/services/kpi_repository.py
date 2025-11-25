# backend_core/services/kpi_repository.py

from backend_core.services.supabase_client import table

SESSIONS_TABLE = "ca_sessions"
PAYMENTS_TABLE = "ca_payment_sessions"
WALLETS_TABLE = "ca_wallets"

# ============================================================
# SESSION KPIs
# ============================================================

def kpi_sessions_active():
    resp = (
        table(SESSIONS_TABLE)
        .select("id")
        .eq("status", "active")
        .execute()
    )
    return len(resp.data or [])


def kpi_sessions_finished():
    resp = (
        table(SESSIONS_TABLE)
        .select("id")
        .eq("status", "finished")
        .execute()
    )
    return len(resp.data or [])


def kpi_sessions_expired():
    """
    Cuenta las sesiones expiradas (no completaron aforo en plazo).
    """
    resp = (
        table(SESSIONS_TABLE)
        .select("id")
        .eq("status", "expired")
        .execute()
    )
    return len(resp.data or [])


# ============================================================
# PAYMENT KPIs
# ============================================================

def kpi_payment_deposit_ok():
    resp = (
        table(PAYMENTS_TABLE)
        .select("id")
        .eq("status", "deposit_ok")
        .execute()
    )
    return len(resp.data or [])


def kpi_payment_deposit_failed():
    resp = (
        table(PAYMENTS_TABLE)
        .select("id")
        .eq("status", "deposit_failed")
        .execute()
    )
    return len(resp.data or [])


# ============================================================
# WALLET KPIs
# ============================================================

def kpi_wallets_total():
    resp = (
        table(WALLETS_TABLE)
        .select("id")
        .execute()
    )
    return len(resp.data or [])
