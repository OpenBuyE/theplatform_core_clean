# backend_core/services/kpi_repository.py

from backend_core.services.supabase_client import table

SESSIONS_TABLE = "ca_sessions"
PAYMENTS_TABLE = "ca_payment_sessions"
WALLETS_TABLE = "ca_wallets"


# ============================================================
# SESSION KPIs
# ============================================================

def kpi_sessions_active():
    """
    Cuenta sesiones ACTIVAS.
    """
    resp = (
        table(SESSIONS_TABLE)
        .select("id")
        .eq("status", "active")
        .execute()
    )
    return len(resp.data or [])


def kpi_sessions_finished():
    """
    Cuenta sesiones finalizadas.
    """
    resp = (
        table(SESSIONS_TABLE)
        .select("id")
        .eq("status", "finished")
        .execute()
    )
    return len(resp.data or [])


# ============================================================
# PAYMENT KPIs
# ============================================================

def kpi_payment_deposit_ok():
    """
    Pagos cuya fase de DEPOSITO está OK.
    La columna correcta en la tabla es 'status', NO 'state'.
    """
    resp = (
        table(PAYMENTS_TABLE)
        .select("id")
        .eq("status", "deposit_ok")   # 🔥 CORREGIDO 
        .execute()
    )
    return len(resp.data or [])


def kpi_payment_deposit_failed():
    """
    Pagos fallidos en la fase de DEPOSITO.
    """
    resp = (
        table(PAYMENTS_TABLE)
        .select("id")
        .eq("status", "deposit_failed")   # 🔥 CORREGIDO
        .execute()
    )
    return len(resp.data or [])


# ============================================================
# WALLET KPIs
# ============================================================

def kpi_wallets_total():
    """
    Total wallets creadas.
    """
    resp = (
        table(WALLETS_TABLE)
        .select("id")
        .execute()
    )
    return len(resp.data or [])
