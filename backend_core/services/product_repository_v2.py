# backend_core/services/product_repository_v2.py

from datetime import datetime
from backend_core.services.supabase_client import table

PRODUCTS_TABLE = "products_v2"
CATEGORIES_TABLE = "categorias_v2"
PROVIDERS_TABLE = "providers_v2"


# ============================================================
# LISTAR PRODUCTOS
# ============================================================
def list_products_v2():
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []


# ============================================================
# LISTAR CATEGORÍAS
# ============================================================
def list_categories():
    resp = (
        table(CATEGORIES_TABLE)
        .select("*")
        .order("nombre")
        .execute()
    )
    return resp.data or []


# ============================================================
# LISTAR PROVIDERS
# ============================================================
def list_providers_safe():
    resp = (
        table(PROVIDERS_TABLE)
        .select("*")
        .order("nombre")
        .execute()
    )
    return resp.data or []


# ============================================================
# OBTENER PRODUCTO POR ID
# ============================================================
def get_product_v2(product_id: str):
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .eq("id", product_id)
        .single()
        .execute()
    )
    return resp.data


# ============================================================
# OBTENER CATEGORÍA POR ID
# ============================================================
def get_category_by_id(category_id: str):
    resp = (
        table(CATEGORIES_TABLE)
        .select("*")
        .eq("id", category_id)
        .single()
        .execute()
    )
    return resp.data


# ============================================================
# OBTENER PROVIDER POR ID
# ============================================================
def get_provider_by_id(provider_id: str):
    resp = (
        table(PROVIDERS_TABLE)
        .select("*")
        .eq("id", provider_id)
        .single()
        .execute()
    )
    return resp.data


# ============================================================
# FILTRADO AVANZADO DE PRODUCTOS
# ============================================================
def filter_products(category_id=None, provider_id=None, active_only=False):
    qb = table(PRODUCTS_TABLE).select("*")

    if category_id:
        qb = qb.eq("category_id", category_id)

    if provider_id:
        qb = qb.eq("provider_id", provider_id)

    if active_only:
        qb = qb.eq("active", True)

    qb = qb.order("created_at", desc=True)

    resp = qb.execute()
    return resp.data or []


# ============================================================
# CREAR CATEGORÍA
# ============================================================
def create_category(nombre: str, descripcion: str = ""):
    payload = {
        "nombre": nombre,
        "descripcion": descripcion,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }

    resp = table(CATEGORIES_TABLE).execute(
        method="POST", json=payload
    )
    return resp.data


# ============================================================
# ACTUALIZAR CATEGORÍA
# ============================================================
def update_category(category_id: str, nombre: str, descripcion: str):
    payload = {
        "nombre": nombre,
        "descripcion": descripcion
    }

    resp = (
        table(CATEGORIES_TABLE)
        .eq("id", category_id)
        .execute(method="PATCH", json=payload)
    )
    return resp.data


# ============================================================
# ELIMINAR CATEGORÍA
# (no hay DELETE → hacemos soft delete)
# ============================================================
def delete_category(category_id: str):
    payload = {"is_active": False}

    resp = (
        table(CATEGORIES_TABLE)
        .eq("id", category_id)
        .execute(method="PATCH", json=payload)
    )
    return resp.data


# ============================================================
# CREAR PRODUCTO
# ============================================================
def create_product(
    name: str,
    description: str,
    price_final: float,
    provider_id: str,
    organization_id: str,
    category_id: str = None,
    image_url: str = None,
    currency: str = "EUR",
    sku: str = None
):
    payload = {
        "name": name,
        "description": description,
        "price_final": price_final,
        "provider_id": provider_id,
        "organization_id": organization_id,
        "category_id": category_id,
        "image_url": image_url,
        "currency": currency,
        "sku": sku,
        "active": True,
        "created_at": datetime.utcnow().isoformat(),
    }

    resp = table(PRODUCTS_TABLE).execute(method="POST", json=payload)
    return resp.data
