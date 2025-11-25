# backend_core/services/product_repository_v2.py

from backend_core.services.supabase_client import table

PRODUCTS_TABLE = "products_v2"
CATEGORIES_TABLE = "categorias_v2"


# =======================================================
# LISTAR CATEGORÍAS (usa tus columnas exactas)
# =======================================================
def list_categories():
    try:
        resp = (
            table(CATEGORIES_TABLE)
            .select("*")
            .order("nombre", desc=False)
            .execute()
        )
        rows = resp.data or []

        # Normalizamos salida:
        normalized = []
        for r in rows:
            normalized.append({
                "id": r.get("id"),
                "name": r.get("nombre"),         # ← nombre REAL
                "description": r.get("descripcion"),
                "is_active": r.get("is_active"),
                "raw": r,
            })

        return normalized

    except Exception as e:
        print("ERROR en list_categories:", e)
        return []


# =======================================================
# LISTAR PRODUCTOS
# =======================================================
def list_products_v2():
    try:
        resp = (
            table(PRODUCTS_TABLE)
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        print("ERROR list_products_v2:", e)
        return []


# =======================================================
# FILTRAR PRODUCTOS POR CATEGORIA
# =======================================================
def filter_products(category_id: str):
    try:
        resp = (
            table(PRODUCTS_TABLE)
            .select("*")
            .eq("category_id", category_id)
            .order("created_at", desc=True)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        print("ERROR filter_products:", e)
        return []


# =======================================================
# OBTENER PRODUCTO POR ID
# =======================================================
def get_product_v2(product_id: str):
    try:
        resp = (
            table(PRODUCTS_TABLE)
            .select("*")
            .eq("id", product_id)
            .single()
            .execute()
        )
        return resp.data
    except Exception as e:
        print("ERROR get_product_v2:", e)
        return None


# =======================================================
# CREAR PRODUCTO
# =======================================================
def create_product(product: dict):
    """
    product = {
        "organization_id": "111...",
        "provider_id": "222...",
        "sku": "...",
        "name": "...",
        "description": "...",
        "price_final": 100,
        "price_base": 82.64,
        "vat_rate": 21,
        "currency": "EUR",
        "image_url": "https://...",
        "category_id": "...",
        "active": True
    }
    """
    try:
        resp = (
            table(PRODUCTS_TABLE)
            .insert(product)
            .execute()
        )
        return resp.data
    except Exception as e:
        print("ERROR create_product:", e)
        return None
