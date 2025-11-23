# backend_core/services/product_repository.py

from __future__ import annotations

from typing import Optional, Dict, List
from backend_core.services import supabase_client


PRODUCTS_TABLE = "products_v2"


def get_product(product_id: str) -> Optional[Dict]:
    resp = (
        supabase_client.table(PRODUCTS_TABLE)
        .select("*")
        .eq("id", product_id)
        .single()
        .execute()
    )
    return resp.data


def list_products(organization_id: str) -> List[Dict]:
    resp = (
        supabase_client.table(PRODUCTS_TABLE)
        .select("*")
        .eq("organization_id", organization_id)
        .order("created_at")
        .execute()
    )
    return resp.data or []
