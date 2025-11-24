# backend_core/services/product_seeder.py

from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event

PRODUCTS_TABLE = "products_v2"


def seed_products_v2():
    """Inserta 20 productos fake en products_v2 (solo si no existen)."""

    products = [
        # ELECTRÓNICA
        {
            "organization_id": "11111111-1111-1111-1111-111111111111",
            "provider_id": "22222222-2222-2222-2222-222222222222",
            "sku": "TV-55-SAM-001",
            "name": 'Samsung 55" QLED TV',
            "description": "Televisor QLED 4K con HDR10+",
            "price_final": 699.00,
            "price_base": 577.69,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1587825140708-dfaf72ae4b2a",
            "active": True,
        },
        {
            "organization_id": "11111111-1111-1111-1111-111111111111",
            "provider_id": "22222222-2222-2222-2222-222222222222",
            "sku": "TV-65-LGX-002",
            "name": 'LG OLED 65" EVO',
            "description": "OLED EVO 4K Premium",
            "price_final": 1699.00,
            "price_base": 1403.31,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1593305841991-05c0216f4c86",
            "active": True,
        },
        # SMARTPHONES
        {
            "organization_id": "11111111-1111-1111-1111-111111111111",
            "provider_id": "22222222-2222-2222-2222-222222222222",
            "sku": "PH-IP13-003",
            "name": "iPhone 13 128GB",
            "description": "Smartphone Apple 128GB",
            "price_final": 799.00,
            "price_base": 660.33,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9",
            "active": True,
        },
        {
            "organization_id": "11111111-1111-1111-1111-111111111111",
            "provider_id": "22222222-2222-2222-2222-222222222222",
            "sku": "PH-S22-004",
            "name": "Samsung Galaxy S22",
            "description": "Smartphone Samsung gama alta",
            "price_final": 699.00,
            "price_base": 577.69,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1610945265078-7f3c8ec3df0d",
            "active": True,
        },
        # PORTÁTILES
        {
            "organization_id": "11111111-1111-1111-1111-111111111111",
            "provider_id": "22222222-2222-2222-2222-222222222222",
            "sku": "LT-MBA-005",
            "name": 'MacBook Air M2 13"',
            "description": "Portátil Apple M2 8GB/256GB",
            "price_final": 1299.00,
            "price_base": 1073.55,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8",
            "active": True,
        },
        {
            "organization_id": "11111111-1111-1111-1111-111111111111",
            "provider_id": "22222222-2222-2222-2222-222222222222",
            "sku": "LT-ASU-006",
            "name": "ASUS ZenBook 14",
            "description": 'Ultrabook 14" ligero',
            "price_final": 899.00,
            "price_base": 742.15,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1587825140708-dfaf72ae4b2a",
            "active": True,
        },
        # GAMING
        {
            "organization_id": "11111111-1111-1111-1111-111111111111",
            "provider_id": "22222222-2222-2222-2222-222222222222",
            "sku": "GM-PS5-007",
            "name": "PlayStation 5",
            "description": "Consola PS5 Estándar",
            "price_final": 549.00,
            "price_base": 453.72,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1606813907291-d86efa9b94a9",
            "active": True,
        },
        {
            "organization_id": "11111111-1111-1111-1111-111111111111",
            "provider_id": "22222222-2222-2222-2222-222222222222",
            "sku": "GM-XBX-008",
            "name": "Xbox Series X",
            "description": "Consola Microsoft Series X",
            "price_final": 499.00,
            "price_base": 412.40,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1621252179027-944cc673594a",
            "active": True,
        }
        # … puedes añadir más si quieres.
    ]

    inserted = 0

    for p in products:
        existing = (
            table(PRODUCTS_TABLE)
            .select("id")
            .eq("sku", p["sku"])
            .execute()
            .data
        )

        if not existing:
            table(PRODUCTS_TABLE).insert(p).execute()
            inserted += 1

    log_event("PRODUCT_SEEDER", f"{inserted} products inserted into products_v2.")
    return inserted
