# backend_core/services/kpi_repository.py

from backend_core.services.supabase_client import table


SESSIONS_TABLE = "ca_sessions"
PAYMENTS_TABLE = "ca_payment_sessions"


# ===========================================
#   SESSIONS METRICS
# ===========================================
def kpi_sessions_active():
    """
    Número de sesiones actualmente activas.
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
    Número de sesiones finalizadas correctamente.
    """
    resp = (
        table(SESSIONS_TABLE)
        .select("id")
        .eq("status", "finished")
        .execute()
    )
    return len(resp.data or [])


def kpi_sessions_expired():
    """
    Número de sesiones expiradas por timeout (no aforo).
    """
    resp = (
        table(SESSIONS_TABLE)
        .select("id")
        .eq("status", "expired")
        .execute()
    )
    return len(resp.data or [])


# ===========================================
#   PAYMENT METRICS
# ===========================================
def kpi_wallet_deposit_ok():
    """
    Pagos que entraron correctamente a depósito.
    """
    resp = (
        table(PAYMENTS_TABLE)
        .select("id")
        .eq("state", "deposit_ok")
        .execute()
    )
    return len(resp.data or [])


def kpi_wallet_deposit_failed():
    """
    Pagos que fallaron durante el intento de depósito.
    """
    resp = (
        table(PAYMENTS_TABLE)
        .select("id")
        .eq("state", "deposit_failed")
        .execute()
    )
    return len(resp.data or [])


def kpi_wallet_refunds():
    """
    Pagos devueltos (refunds automáticos por expiración o manuales).
    """
    resp = (
        table(PAYMENTS_TABLE)
        .select("id")
        .eq("state", "refunded")
        .execute()
    )
    return len(resp.data or [])


def kpi_wallet_pending():
    """
    Pagos aún en proceso.
    """
    resp = (
        table(PAYMENTS_TABLE)
        .select("id")
        .eq("state", "pending")
        .execute()
    )
    return len(resp.data or [])
