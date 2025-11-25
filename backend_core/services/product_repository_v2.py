# backend_core/services/product_repository_v2.py

from backend_core.services.supabase_client import table
from datetime import datetime

PRODUCTS_TABLE = "products_v2"
CATEGORIES_TABLE = "categorias_v2"
PROVIDERS_TABLE = "ca_operators"   # si tus proveedores van aquí


# ---------------------------------------------------------
# LISTAR CATEGORÍAS
# ---------------------------------------------------------
def list_categories():
    resp = (
        table(CATEGORIES_TABLE)
        .select("id, nombre, descripcion, is_active")
        .order("nombre")
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
# FILTRAR PRODUCTOS POR CATEGORÍA
# ---------------------------------------------------------
def filter_products(category_id: str):
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .eq("category_id", category_id)
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []


# ---------------------------------------------------------
# OBTENER PRODUCTO POR ID
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


# ---------------------------------------------------------
# OBTENER CATEGORÍA POR ID (FALTANTE)
# ---------------------------------------------------------
def get_category_by_id(category_id: str):
    resp = (
        table(CATEGORIES_TABLE)
        .select("id, nombre, descripcion, is_active")
        .eq("id", category_id)
        .single()
        .execute()
    )
    return resp.data


# ---------------------------------------------------------
# OBTENER PROVIDER POR ID (FALTANTE)
# ---------------------------------------------------------
def get_provider_by_id(provider_id: str):
    """
    Si tus proveedores están en ca_operators:
    puedes ajustar campos según tu estructura.
    """
    resp = (
        table(PROVIDERS_TABLE)
        .select("id, name, kyc_status, created_at")
        .eq("id", provider_id)
        .single()
        .execute()
    )
    return resp.data


# ---------------------------------------------------------
# CREAR PRODUCTO PRO
# ---------------------------------------------------------
def create_product(
    name: str,
    description: str,
    price_final: float,
    price_base: float,
    vat_rate: float,
    currency: str,
    sku: str,
    image_url: str,
    organization_id: str,
    provider_id: str,
    category_id: str,
):
    payload = {
        "id": None,  # autogen UUID
        "organization_id": organization_id,
        "provider_id": provider_id,
        "sku": sku,
        "name": name,
        "description": description,
        "price_final": price_final,
        "price_base": price_base,
        "vat_rate": vat_rate,
        "currency": currency,
        "image_url": image_url,
        "active": True,
        "category_id": category_id,
        "created_at": datetime.utcnow().isoformat(),
    }

    resp = table(PRODUCTS_TABLE).insert(payload).execute()
    return resp.data
