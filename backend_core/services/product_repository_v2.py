# backend_core/services/product_repository_v2.py

from backend_core.services.supabase_client import table


# ================================================================
# 📌 LISTAR PRODUCTOS (versión moderna)
# ================================================================

def list_products_v2():
    return (
        table("products_v2")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )


# ================================================================
# 📌 OBTENER PRODUCTO POR ID
# ================================================================

def get_product_v2(product_id: str):
    return (
        table("products_v2")
        .select("*")
        .eq("id", product_id)
        .single()
        .execute()
    )


# ================================================================
# 📌 CREAR PRODUCTO
# ================================================================

def create_product(data: dict):
    return table("products_v2").insert(data).execute()


# ================================================================
# 📌 ACTUALIZAR PRODUCTO
# ================================================================

def update_product(product_id: str, data: dict):
    return (
        table("products_v2")
        .update(data)
        .eq("id", product_id)
        .execute()
    )


# ================================================================
# 📌 CATEGORÍAS
# ================================================================

def list_categories():
    return (
        table("product_categories")
        .select("*")
        .order("name", desc=False)
        .execute()
    )


def create_category(data: dict):
    return table("product_categories").insert(data).execute()


def get_category_by_id(category_id: str):
    return (
        table("product_categories")
        .select("*")
        .eq("id", category_id)
        .single()
        .execute()
    )


# ================================================================
# 📌 FILTRO AVANZADO (buscador profesional)
# ================================================================

def filter_products(text: str = "", category_id: str = None):
    query = table("products_v2").select("*")

    if text:
        query = query.ilike("name", f"%{text}%")

    if category_id:
        query = query.eq("category_id", category_id)

    return query.order("created_at", desc=True).execute()
