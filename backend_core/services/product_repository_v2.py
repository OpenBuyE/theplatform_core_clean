# backend_core/services/product_repository_v2.py

from backend_core.services.supabase_client import table

PRODUCTS_TABLE = "products_v2"
CATEGORIES_TABLE = "categorias_v2"


# ---------------------------------------------------------
# LISTAR CATEGORÍAS (USO EN PRODUCT CATALOG PRO)
# ---------------------------------------------------------
def list_categories():
    """
    Devuelve todas las categorías de categorías_v2.
    Orden temporalmente por ID para evitar problemas de columnas inexistentes.
    """
    resp = (
        table(CATEGORIES_TABLE)
        .select("*")
        .order("id")   # FIX: antes .order("name"), columna inexistente
        .execute()
    )
    return resp.data or []


# ---------------------------------------------------------
# LISTAR PRODUCTOS
# ---------------------------------------------------------
def list_products_v2():
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []


# ---------------------------------------------------------
# PRODUCTOS POR CATEGORÍA
# ---------------------------------------------------------
def list_products_by_category(category_id: str):
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .eq("category_id", category_id)
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []


# ---------------------------------------------------------
# GET PRODUCT
# ---------------------------------------------------------
def get_product_v2(product_id: str):
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .eq("id", product_id)
        .single()
        .execute()
    )
    return resp.data
