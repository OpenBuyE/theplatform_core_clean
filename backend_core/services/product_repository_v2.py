# backend_core/services/product_repository_v2.py

from backend_core.services.supabase_client import table

PRODUCTS_TABLE = "products_v2"
CATEGORIES_TABLE = "categorias_v2"


# ------------------------------------
# BASIC LIST
# ------------------------------------
def list_products():
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []


# ------------------------------------
# CATEGORIES
# ------------------------------------
def list_categories():
    resp = (
        table(CATEGORIES_TABLE)
        .select("*")
        .order("name")
        .execute()
    )
    return resp.data or []


# ------------------------------------
# FILTERED PRODUCTS
# ------------------------------------
def filter_products(category=None, provider=None, active=None, min_price=None, max_price=None):
    q = table(PRODUCTS_TABLE).select("*")

    if category:
        q = q.eq("category_id", category)

    if provider:
        q = q.eq("provider_id", provider)

    if active is not None:
        q = q.eq("active", active)

    if min_price:
        q = q.gte("price_final", min_price)

    if max_price:
        q = q.lte("price_final", max_price)

    resp = q.order("price_final").execute()
    return resp.data or []
