# backend_core/services/product_repository_v2.py

from backend_core.services.supabase_client import table

PRODUCTS_TABLE = "products_v2"
CATEGORIES_TABLE = "categorias_v2"


# ===========================================================
# CATEGORIES
# ===========================================================

def list_categories():
    """Devuelve todas las categorías ordenadas por nombre."""
    resp = (
        table(CATEGORIES_TABLE)
        .select("*")
        .order("categoria")      # columna correcta en categorias_v2
        .execute()
    )
    return resp.data or []


# ===========================================================
# PRODUCTS
# ===========================================================

def list_products(limit: int = 100):
    """Lista productos activos, ordenados por fecha."""
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data or []


def filter_products(category_id: str = None, text: str = None):
    """Filtro: por categoría y texto."""
    query = table(PRODUCTS_TABLE).select("*")

    if category_id:
        query = query.eq("category_id", category_id)

    if text:
        text_pattern = f"%{text.lower()}%"
        query = query.ilike("name", text_pattern)

    resp = query.order("created_at", desc=True).execute()
    return resp.data or []


def get_product_by_id(product_id: str):
    """Devuelve un producto por id."""
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .eq("id", product_id)
        .single()
        .execute()
    )
    return resp.data


# ===========================================================
# CREATE PRODUCT (NUEVO)
# ===========================================================

def create_product(data: dict) -> bool:
    """
    Inserta un producto completo en products_v2.
    Data debe incluir:
      id, organization_id, provider_id, category_id,
      sku, name, description, price_final, price_base,
      vat_rate, currency, image_url
    """
    try:
        resp = (
            table(PRODUCTS_TABLE)
            .insert(data)
            .execute()
        )
        return resp.data is not None
    except Exception as e:
        print("ERROR create_product:", e)
        return False
