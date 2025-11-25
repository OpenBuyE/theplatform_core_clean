# backend_core/services/kpi_repository.py

from backend_core.services.supabase_client import table

SESSIONS_TABLE = "ca_sessions"
PAYMENT_SESSIONS_TABLE = "ca_payment_sessions"
MODULES_TABLE = "ca_modules"
OPERATORS_TABLE = "ca_operators"
PARTICIPANTS_TABLE = "ca_session_participants"


# -----------------------------
#   KPI: SESIONES
# -----------------------------

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
    resp = (
        table(SESSIONS_TABLE)
        .select("id")
        .eq("status", "expired")
        .execute()
    )
    return len(resp.data or [])


# -----------------------------
#   KPI: PARTICIPANTES
# -----------------------------

def kpi_participants_total():
    resp = (
        table(PARTICIPANTS_TABLE)
        .select("id")
        .execute()
    )
    return len(resp.data or [])


# -----------------------------
#   KPI: MÓDULOS
# -----------------------------

def kpi_modules_total():
    resp = (
        table(MODULES_TABLE)
        .select("id")
        .execute()
    )
    return len(resp.data or [])


# -----------------------------
#   KPI: OPERADORES
# -----------------------------

def kpi_operators_total():
    resp = (
        table(OPERATORS_TABLE)
        .select("id")
        .execute()
    )
    return len(resp.data or [])


# -----------------------------
#   KPI: PAYMENTS (si aplica)
# -----------------------------

def kpi_payments_total():
    """Simplemente contar registros en ca_payment_sessions"""
    try:
        resp = (
            table(PAYMENT_SESSIONS_TABLE)
            .select("id")
            .execute()
        )
        return len(resp.data or [])
    except Exception:
        return 0
