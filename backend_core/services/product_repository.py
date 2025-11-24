# backend_core/services/product_repository.py

from __future__ import annotations

from typing import List, Optional, Dict, Any

from backend_core.services.supabase_client import table

PRODUCTS_TABLE = "products_v2"


def get_product(product_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un producto según su ID (TEXT, no UUID).
    """
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .eq("id", product_id)
        .single()
        .execute()
    )

    # Si no existen datos, resp.data será None o lista vacía
    if not resp.data:
        return None

    # resp.data es un dict (single)
    return resp.data


def list_products() -> List[Dict[str, Any]]:
    """
    Lista todos los productos para dropdowns.
    """
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .order("name")
        .execute()
    )

    if not resp.data:
        return []

    return resp.data
