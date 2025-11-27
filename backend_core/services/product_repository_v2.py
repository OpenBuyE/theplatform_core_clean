# backend_core/services/product_repository_v2.py

from backend_core.services.supabase_client import table

# ================================================================
# 📌 PRODUCTOS
# ================================================================

def list_products_v2():
    return (
        table("products_v2")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )


def get_product_v2(product_id: str):
    return (
        table("products_v2")
        .select("*")
        .eq("id", product_id)
        .single()
        .execute()
    )


# Alias moderno
def get_product(product_id: str):
    return get_product_v2(product_id)


def create_product(data: dict):
    return table("products_v2").insert(data).execute()


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


def update_category(category_id: str, data: dict):
    return (
        table("product_categories")
        .update(data)
        .eq("id", category_id)
        .execute()
    )


def get_category_by_id(category_id: str):
    return (
        table("product_categories")
        .select("*")
        .eq("id", category_id)
        .single()
        .execute()
    )


# ================================================================
# 📌 PROVEEDORES
# ================================================================

def list_providers_v2():
    return (
        table("providers_v2")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )


def get_provider_by_id(provider_id: str):
    return (
        table("providers_v2")
        .select("*")
        .eq("id", provider_id)
        .single()
        .execute()
    )


# ================================================================
# 📌 BUSCADOR / FILTRO AVANZADO
# ================================================================

def filter_products(text: str = "", category_id: str = None):
    q = table("products_v2").select("*")

    if text:
        q = q.ilike("name", f"%{text}%")

    if category_id:
        q = q.eq("category_id", category_id)

    return q.order("created_at", desc=True).execute()
