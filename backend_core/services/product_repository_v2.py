# backend_core/services/product_repository_v2.py

from backend_core.services.supabase_client import table


# ======================================================
# PRODUCTOS — LISTADO
# ======================================================

def list_products():
    return (
        table("ca_products")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )


# ======================================================
# FILTRO PARA PRODUCT CATALOG PRO
# ======================================================

def filter_products(search: str = "", category: str = None):
    q = table("ca_products").select("*")

    if search:
        q = q.ilike("name", f"%{search}%")

    if category:
        q = q.eq("category_id", category)

    return q.order("created_at", desc=True).execute()


# ======================================================
# CRUD PRODUCTOS
# ======================================================

def create_product(data: dict):
    """
    Compatible con el código legacy que llama create_product()
    """
    return (
        table("ca_products")
        .insert(data)
        .execute()
    )


def get_product(product_id: str):
    return (
        table("ca_products")
        .select("*")
        .eq("id", product_id)
        .single()
        .execute()
    )


# ======================================================
# CATEGORÍAS
# ======================================================

def list_categories():
    return (
        table("ca_categories")
        .select("*")
        .order("name", asc=True)
        .execute()
    )


def get_category_by_id(category_id: str):
    return (
        table("ca_categories")
        .select("*")
        .eq("id", category_id)
        .single()
        .execute()
    )
