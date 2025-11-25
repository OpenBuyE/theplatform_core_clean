# backend_core/services/product_repository_v2.py

from backend_core.services.supabase_client import table

PRODUCTS_TABLE = "products_v2"
CATEGORIES_TABLE = "categorias_v2"
OPERATORS_TABLE = "ca_operators"


# =====================================================
# LISTAR PRODUCTOS (todos)
# =====================================================
def list_products_v2():
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []


# Alias por compatibilidad, por si algún código antiguo usa list_products()
def list_products():
    return list_products_v2()


# =====================================================
# LISTAR CATEGORÍAS
#  (no asumimos nombre: seleccionamos todo y ordenamos por id)
# =====================================================
def list_categories():
    resp = (
        table(CATEGORIES_TABLE)
        .select("*")
        .order("id")
        .execute()
    )
    return resp.data or []


# =====================================================
# LISTAR PRODUCTOS POR CATEGORÍA
# =====================================================
def list_products_by_category(category_id: str):
    if not category_id:
        return list_products_v2()

    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .eq("category_id", category_id)
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []


# =====================================================
# FILTRADO AVANZADO
#  (category_id, rango de precios, búsqueda por nombre)
# =====================================================
def filter_products(category_id=None, min_price=None, max_price=None, search=None):
    q = table(PRODUCTS_TABLE).select("*")

    if category_id:
        q = q.eq("category_id", category_id)

    if search:
        # asumimos campo name (si luego vemos que no existe, lo ajustamos)
        q = q.ilike("name", f"%{search}%")

    if min_price is not None:
        q = q.gte("price_final", min_price)

    if max_price is not None:
        q = q.lte("price_final", max_price)

    resp = q.order("created_at", desc=True).execute()
    return resp.data or []


# =====================================================
# OBTENER PRODUCTO POR ID (usa id, NO product_id)
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
