# backend_core/services/product_seeder.py

import uuid
from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event

PRODUCTS_TABLE = "products_v2"

def seed_products(products: list[dict]):
    inserted = 0
    for p in products:
        # Evitar duplicados por SKU
        existing = (
            table(PRODUCTS_TABLE)
            .select("id")
            .eq("sku", p["sku"])
            .execute()
            .data
        )
        if existing:
            continue

        table(PRODUCTS_TABLE).insert(p).execute()
        inserted += 1

    log_event("PRODUCT_SEEDER", f"{inserted} products inserted.")
    return inserted
