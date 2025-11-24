# backend_core/services/product_repository.py

from typing import List, Dict, Optional

from backend_core.services.supabase_client import table

PRODUCTS_TABLE = "products_v2"


def list_products(only_active: bool = True) -> List[Dict]:
    q = table(PRODUCTS_TABLE).select("*")
    if only_active:
        q = q.eq("active", True)
    resp = q.execute()
    return resp.data or []


def get_product(product_id: str) -> Optional[Dict]:
    """
    Obtiene un producto por su id (text).
    """
    if not product_id:
        return None
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .eq("id", product_id)
        .execute()
    )
    data = resp.data or []
    if isinstance(data, list):
        return data[0] if data else None
    return data
