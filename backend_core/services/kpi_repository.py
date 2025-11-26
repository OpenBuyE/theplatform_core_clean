# backend_core/services/kpi_repository.py

from backend_core.services.supabase_client import table


# ============================
# Helpers internos
# ============================

def _count_rows(tbl_name: str, **filters) -> int:
    q = table(tbl_name).select("id")
    for col, value in filters.items():
        q = q.eq(col, value)
    rows = q.execute()
    return len(rows) if rows else 0


# ============================
# KPIs de sesiones
# ============================

def sessions_active(operator_id: str | None = None) -> int:
    # Por ahora no filtramos por operator_id; la segmentación se hace aguas arriba.
    return _count_rows("ca_sessions", status="active")


def sessions_finished(operator_id: str | None = None) -> int:
    return _count_rows("ca_sessions", status="finished")


def sessions_expired(operator_id: str | None = None) -> int:
    return _count_rows("ca_sessions", status="expired")


# Aliases esperados por las vistas antiguas
def get_kpi_sessions_active(operator_id: str | None = None) -> int:
    return sessions_active(operator_id)


def get_kpi_sessions_finished(operator_id: str | None = None) -> int:
    return sessions_finished(operator_id)


def get_kpi_sessions_expired(operator_id: str | None = None) -> int:
    return sessions_expired(operator_id)


# ============================
# KPIs de wallet
# ============================

def wallet_deposit_ok(operator_id: str | None = None) -> int:
    # Ejemplo: nº de sesiones con depósito OK (si tienes otra lógica, la ajustamos luego)
    return _count_rows("ca_payment_sessions", status="deposit_ok")


def wallets_total(operator_id: str | None = None) -> int:
    return _count_rows("ca_wallets")


# ============================
# KPIs de catálogo
# ============================

def providers_total(operator_id: str | None = None) -> int:
    return _count_rows("providers_v2", active=True)


def products_total(operator_id: str | None = None) -> int:
    return _count_rows("products_v2", active=True)


def categories_total(operator_id: str | None = None) -> int:
    return _count_rows("categorias_v2", is_active=True)
