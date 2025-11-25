# backend_core/services/product_repository_v2.py

from backend_core.services.supabase_client import table


PRODUCTS_TABLE = "products_v2"
CATEGORIES_TABLE = "categorias_v2"
OPERATORS_TABLE = "ca_operators"


# =====================================================
# LISTAR PRODUCTOS (todos)
# =====================================================
def list_products():
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []


# =====================================================
# LISTAR CATEGORÍAS
# =====================================================
def list_categories():
    resp = (
        table(CATEGORIES_TABLE)
        .select("id, name")
        .order("name")
        .execute()
    )
    return resp.data or []


# =====================================================
# FILTRADO AVANZADO (categoría, precio, nombre)
# =====================================================
def filter_products(category_id=None, min_price=None, max_price=None, search=None):
    q = table(PRODUCTS_TABLE).select("*")

    # filtro por categoría
    if category_id:
        q = q.eq("category_id", category_id)

    # búsqueda por texto (nombre o descripción)
    if search:
        # Supabase: ilike → case-insensitive (SQL LIKE)
        q = q.ilike("name", f"%{search}%")

    # precio mínimo
    if min_price is not None:
        q = q.gte("price_final", min_price)

    # precio máximo
    if max_price is not None:
        q = q.lte("price_final", max_price)

    resp = q.order("created_at", desc=True).execute()
    return resp.data or []


# =====================================================
# OBTENER PRODUCTO POR ID
# =====================================================
def get_product_v2(product_id: str):
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .eq("id", product_id)
        .single()
        .execute()
    )
    return resp.data


# =====================================================
# GET CATEGORY BY ID
# =====================================================
def get_category_by_id(category_id: str):
    if not category_id:
        return None

    resp = (
        table(CATEGORIES_TABLE)
        .select("*")
        .eq("id", category_id)
        .single()
        .execute()
    )
    return resp.data


# =====================================================
# GET PROVIDER (OPERATOR) BY ID
# =====================================================
def get_provider_by_id(provider_id: str):
    if not provider_id:
        return None

    resp = (
        table(OPERATORS_TABLE)
        .select("*")
        .eq("id", provider_id)
        .single()
        .execute()
    )
    return resp.data
