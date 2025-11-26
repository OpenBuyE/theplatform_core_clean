# backend_core/services/product_repository_v2.py

from datetime import datetime
from backend_core.services.supabase_client import client, table


PRODUCTS_TABLE = "products_v2"
CATEGORIES_TABLE = "categorias_v2"
PROVIDERS_TABLE = "providers_v2"


# =========================================================
# CATEGORIES — CRUD COMPLETO
# =========================================================

def list_categories():
    """Devuelve todas las categorías activas ordenadas por nombre"""
    resp = (
        table(CATEGORIES_TABLE)
        .select("*")
        .eq("is_active", True)
        .order("nombre")
        .execute()
    )
    return resp.data or []


def get_category_by_id(category_id: str):
    resp = (
        table(CATEGORIES_TABLE)
        .select("*")
        .eq("id", category_id)
        .single()
        .execute()
    )
    return resp.data


def create_category(nombre: str, descripcion: str = None):
    """Inserta categoría usando POST REST (no insert)"""
    payload = {
        "nombre": nombre,
        "descripcion": descripcion,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }

    r = client.post(f"/rest/v1/{CATEGORIES_TABLE}", json=payload)

    if r.status_code >= 300:
        raise Exception(f"Supabase error {r.status_code}: {r.text}")

    return True


def update_category(category_id: str, nombre: str, descripcion: str, is_active: bool):
    payload = {
        "nombre": nombre,
        "descripcion": descripcion,
        "is_active": is_active,
        "created_at": datetime.utcnow().isoformat()
    }

    r = client.patch(
        f"/rest/v1/{CATEGORIES_TABLE}?id=eq.{category_id}",
        json=payload
    )

    if r.status_code >= 300:
        raise Exception(f"Supabase error {r.status_code}: {r.text}")

    return True


def delete_category(category_id: str):
    r = client.delete(
        f"/rest/v1/{CATEGORIES_TABLE}?id=eq.{category_id}"
    )

    if r.status_code >= 300:
        raise Exception(f"Supabase error {r.status_code}: {r.text}")

    return True


# =========================================================
# PROVIDERS — CRUD COMPLETO
# =========================================================

def list_providers():
    """Lista providers activos"""
    resp = (
        table(PROVIDERS_TABLE)
        .select("*")
        .eq("is_active", True)
        .order("nombre")
        .execute()
    )
    return resp.data or []


def get_provider_by_id(provider_id: str):
    resp = (
        table(PROVIDERS_TABLE)
        .select("*")
        .eq("id", provider_id)
        .single()
        .execute()
    )
    return resp.data


def create_provider(nombre: str, descripcion: str = None):
    payload = {
        "nombre": nombre,
        "descripcion": descripcion,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }

    r = client.post(f"/rest/v1/{PROVIDERS_TABLE}", json=payload)

    if r.status_code >= 300:
        raise Exception(f"Supabase error {r.status_code}: {r.text}")

    return True


def update_provider(provider_id: str, nombre: str, descripcion: str, is_active: bool):
    payload = {
        "nombre": nombre,
        "descripcion": descripcion,
        "is_active": is_active
    }

    r = client.patch(
        f"/rest/v1/{PROVIDERS_TABLE}?id=eq.{provider_id}",
        json=payload
    )

    if r.status_code >= 300:
        raise Exception(f"Supabase error {r.status_code}: {r.text}")

    return True


def delete_provider(provider_id: str):
    r = client.delete(f"/rest/v1/{PROVIDERS_TABLE}?id=eq.{provider_id}")

    if r.status_code >= 300:
        raise Exception(f"Supabase error {r.status_code}: {r.text}")

    return True


# =========================================================
# PRODUCTS — CRUD Y FILTROS
# =========================================================

def list_products():
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []


def get_product_v2(product_id: str):
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .eq("id", product_id)
        .single()
        .execute()
    )
    return resp.data


def filter_products(category_id=None, provider_id=None, active_only=True):
    q = table(PRODUCTS_TABLE).select("*")

    if active_only:
        q = q.eq("active", True)

    if category_id:
        q = q.eq("category_id", category_id)

    if provider_id:
        q = q.eq("provider_id", provider_id)

    resp = q.order("created_at", desc=True).execute()

    return resp.data or []


def create_product(
    organization_id: str,
    provider_id: str,
    name: str,
    description: str,
    price_final: float,
    price_base: float = None,
    vat_rate: float = None,
    currency: str = "EUR",
    sku: str = None,
    image_url: str = None,
    category_id: str = None
):
    payload = {
        "organization_id": organization_id,
        "provider_id": provider_id,
        "name": name,
        "description": description,
        "price_final": price_final,
        "price_base": price_base,
        "vat_rate": vat_rate,
        "currency": currency,
        "sku": sku,
        "image_url": image_url,
        "category_id": category_id,
        "active": True,
        "created_at": datetime.utcnow().isoformat()
    }

    r = client.post(f"/rest/v1/{PRODUCTS_TABLE}", json=payload)

    if r.status_code >= 300:
        raise Exception(f"Supabase error {r.status_code}: {r.text}")

    return True


def update_product(product_id: str, payload: dict):
    r = client.patch(
        f"/rest/v1/{PRODUCTS_TABLE}?id=eq.{product_id}",
        json=payload
    )

    if r.status_code >= 300:
        raise Exception(f"Supabase error {r.status_code}: {r.text}")

    return True


def delete_product(product_id: str):
    r = client.delete(
        f"/rest/v1/{PRODUCTS_TABLE}?id=eq.{product_id}"
    )

    if r.status_code >= 300:
        raise Exception(f"Supabase error {r.status_code}: {r.text}")

    return True
