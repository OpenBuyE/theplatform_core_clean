# backend_core/services/kpi_repository.py

from backend_core.services.supabase_client import table


# ---------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------
def _fetch_one(query):
    try:
        result = query.execute()
        return result[0] if result else None
    except:
        return None


def _fetch_many(query):
    try:
        result = query.execute()
        return result if result else []
    except:
        return []


# ---------------------------------------------------------
# KPI — Sesiones
# ---------------------------------------------------------
def get_kpi_sessions_active(country=None):
    q = table("ca_sessions").select("id", count="exact").eq("status", "active")
    if country:
        q = q.eq("country", country)
    res = q.execute()
    return res.count if hasattr(res, "count") else 0


def get_kpi_sessions_finished(country=None):
    q = table("ca_sessions").select("id", count="exact").eq("status", "finished")
    if country:
        q = q.eq("country", country)
    res = q.execute()
    return res.count if hasattr(res, "count") else 0


def get_kpi_sessions_expired(country=None):
    q = table("ca_sessions").select("id", count="exact").eq("status", "expired")
    if country:
        q = q.eq("country", country)
    res = q.execute()
    return res.count if hasattr(res, "count") else 0


def get_kpi_sessions_parked(country=None):
    q = table("ca_sessions").select("id", count="exact").eq("status", "parked")
    if country:
        q = q.eq("country", country)
    res = q.execute()
    return res.count if hasattr(res, "count") else 0


# ---------------------------------------------------------
# KPI — Productos
# ---------------------------------------------------------
def get_kpi_products_total(country=None):
    q = table("products_v2").select("id", count="exact")
    if country:
        q = q.eq("country", country)
    res = q.execute()
    return res.count if hasattr(res, "count") else 0


# ---------------------------------------------------------
# KPI — Proveedores
# ---------------------------------------------------------
def get_kpi_providers_total(country=None):
    q = table("providers_v2").select("id", count="exact")
    if country:
        q = q.eq("country", country)
    res = q.execute()
    return res.count if hasattr(res, "count") else 0


# ---------------------------------------------------------
# KPI — Categorías
# ---------------------------------------------------------
def get_kpi_categories_total():
    res = table("categorias_v2").select("id", count="exact").execute()
    return res.count if hasattr(res, "count") else 0


# ---------------------------------------------------------
# KPI — Wallets (placeholder operativo)
# ---------------------------------------------------------
def get_kpi_wallets_total(country=None):
    """
    Placeholder. En el futuro leerá de wallets reales.
    De momento contamos usuarios con wallet asociada.
    """
    q = table("app_users_v2").select("id", count="exact")
    if country:
        q = q.eq("country", country)
    res = q.execute()
    return res.count if hasattr(res, "count") else 0


# ---------------------------------------------------------
# KPI — Operadores
# ---------------------------------------------------------
def get_kpi_operators_total(country=None):
    q = table("ca_operators").select("id", count="exact").eq("active", True)
    if country:
        q = q.eq("country", country)
    res = q.execute()
    return res.count if hasattr(res, "count") else 0
