# backend_core/services/product_repository_v2.py

from typing import List, Dict, Any, Optional
from backend_core.services.supabase_client import table


# ============================
# CATEGORÍAS
# ============================

def list_categories() -> List[Dict[str, Any]]:
    rows = table("categorias_v2").select("*").order("created_at", desc=True).execute()
    return rows or []


def create_category(name: str, description: str = "", is_active: bool = True) -> Dict[str, Any]:
    rows = table("categorias_v2").insert(
        {
            "nombre": name,
            "descripcion": description,
            "is_active": is_active,
        }
    ).execute()
    if not rows:
        raise RuntimeError("No se pudo crear la categoría.")
    return rows[0]


def update_category(category_id: str, **fields) -> Dict[str, Any]:
    rows = table("categorias_v2").update(fields).eq("id", category_id).execute()
    if not rows:
        raise RuntimeError("No se pudo actualizar la categoría.")
    return rows[0]


def delete_category(category_id: str):
    table("categorias_v2").update({"is_active": False}).eq("id", category_id).execute()


def get_category_by_id(category_id: str) -> Optional[Dict[str, Any]]:
    rows = table("categorias_v2").select("*").eq("id", category_id).execute()
    return rows[0] if rows else None


# ============================
# PROVEEDORES (vía products_v2)
# ============================

def list_providers_v2() -> List[Dict[str, Any]]:
    """
    Devuelve todos los proveedores desde providers_v2.
    (usado por Product Catalog Pro)
    """
    rows = table("providers_v2").select("*").order("created_at", desc=True).execute()
    return rows or []


def get_provider_by_id(provider_id: str) -> Optional[Dict[str, Any]]:
    rows = table("providers_v2").select("*").eq("id", provider_id).execute()
    return rows[0] if rows else None


# ============================
# PRODUCTOS
# ============================

def list_products_v2() -> List[Dict[str, Any]]:
    rows = (
        table("products_v2")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return rows or []


def create_product(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows = table("products_v2").insert(payload).execute()
    if not rows:
        raise RuntimeError("No se pudo crear el producto.")
    return rows[0]


def get_product_v2(product_id: str) -> Optional[Dict[str, Any]]:
    rows = table("products_v2").select("*").eq("id", product_id).execute()
    return rows[0] if rows else None


def filter_products(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    q = table("products_v2").select("*")
    for col, value in filters.items():
        if value is None:
            continue
        q = q.eq(col, value)
    rows = q.execute()
    return rows or []
