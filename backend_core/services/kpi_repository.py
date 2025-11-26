import typing as t
from backend_core.services.supabase_client import table
from backend_core.services.operator_repository import (
    get_operator_allowed_countries,
    ensure_country_filter,
)

# =========================================================
# HELPERS INTERNOS
# =========================================================

def _safe_data(resp):
    """Compatibilidad con diferentes formatos del wrapper Supabase REST."""
    if hasattr(resp, "data"):
        return resp.data
    return resp.get("data")


def _safe_count(resp) -> int:
    """
    Intenta devolver un count exacto:
    - Si el wrapper tiene resp.count → lo usa
    - Si no, cuenta len(data)
    """
    if hasattr(resp, "count") and resp.count is not None:
        return resp.count

    data = _safe_data(resp) or []
    if isinstance(data, list):
        return len(data)
    return 0


def _resolve_allowed(operator_id: t.Optional[str]) -> t.Optional[t.List[str]]:
    """
    Si operator_id es None → sin filtro (modo global, compatible hacia atrás).
    Si tiene valor → usa get_operator_allowed_countries().

    Esto permite usar los KPIs tanto en modo legacy (sin operador)
    como en modo multi-país (con operador).
    """
    if not operator_id:
        return None
    return get_operator_allowed_countries(operator_id)


# =========================================================
# SESSIONS KPIs
# =========================================================

def sessions_active(operator_id: t.Optional[str] = None) -> int:
    """
    Nº de sesiones activas.
    Si operator_id se pasa → solo del país / países de ese operador.
    """
    allowed = _resolve_allowed(operator_id)

    qb = (
        table("ca_sessions")
        .select("id", count="exact")
        .eq("status", "active")
    )
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_count(resp)


def sessions_finished(operator_id: t.Optional[str] = None) -> int:
    """
    Nº de sesiones finalizadas.
    """
    allowed = _resolve_allowed(operator_id)

    qb = (
        table("ca_sessions")
        .select("id", count="exact")
        .eq("status", "finished")
    )
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_count(resp)


def sessions_expired(operator_id: t.Optional[str] = None) -> int:
    """
    Nº de sesiones expiradas.
    """
    allowed = _resolve_allowed(operator_id)

    qb = (
        table("ca_sessions")
        .select("id", count="exact")
        .eq("status", "expired")
    )
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_count(resp)


# =========================================================
# WALLET / PAYMENTS KPIs (BÁSICOS)
# =========================================================

def wallet_deposit_ok(operator_id: t.Optional[str] = None) -> int:
    """
    Nº de pagos con depósito OK.

    Asumimos tabla: ca_payment_sessions
    y un campo 'status' con valor 'deposit_ok'.
    Si tu esquema real usa otros nombres, aquí solo tendrías que ajustar
    el EQ correspondiente.
    """
    allowed = _resolve_allowed(operator_id)

    qb = (
        table("ca_payment_sessions")
        .select("id", count="exact")
        .eq("status", "deposit_ok")
    )
    # Si ca_payment_sessions también tiene country_code → se filtrará.
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_count(resp)


def wallets_total(operator_id: t.Optional[str] = None) -> int:
    """
    KPI aproximado de nº de wallets / usuarios con sesiones de pago.
    Aquí se cuenta el número total de registros en ca_payment_sessions.
    Si en tu esquema existe una tabla específica de wallets, bastaría
    con cambiar 'ca_payment_sessions' por esa tabla y ajustar.
    """
    allowed = _resolve_allowed(operator_id)

    qb = (
        table("ca_payment_sessions")
        .select("id", count="exact")
    )
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_count(resp)


# =========================================================
# ENTIDADES DE CATÁLOGO
# =========================================================

def products_total(operator_id: t.Optional[str] = None) -> int:
    """
    Nº total de productos visibles para el operador (multi-país).
    """
    allowed = _resolve_allowed(operator_id)

    qb = table("products_v2").select("id", count="exact")
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_count(resp)


def providers_total(operator_id: t.Optional[str] = None) -> int:
    """
    Nº total de proveedores visibles para el operador.
    """
    allowed = _resolve_allowed(operator_id)

    qb = table("providers_v2").select("id", count="exact")
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_count(resp)


def categories_total(operator_id: t.Optional[str] = None) -> int:
    """
    Nº total de categorías visibles para el operador.
    """
    allowed = _resolve_allowed(operator_id)

    qb = table("categorias_v2").select("id", count="exact")
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_count(resp)
