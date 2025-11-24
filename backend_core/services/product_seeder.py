# backend_core/services/product_seeder.py

from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event

PRODUCTS_TABLE = "products_v2"

ORG_ID = "11111111-1111-1111-1111-111111111111"
PROVIDER_ID = "22222222-2222-2222-2222-222222222222"


def seed_products_v2():
    """
    Inserta ~20 productos fake realistas en products_v2.
    Solo inserta si el SKU no existe (idempotente).
    """

    products = [
        # TV & AUDIO
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "TV-55-SAM-001",
            "name": 'Samsung 55" QLED 4K',
            "description": "Televisor QLED 4K con HDR10+ y Smart TV.",
            "price_final": 699.00,
            "price_base": 577.69,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d6",
            "active": True,
        },
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "TV-65-LG-002",
            "name": 'LG OLED 65" EVO',
            "description": "OLED EVO 4K, Dolby Vision, Dolby Atmos.",
            "price_final": 1699.00,
            "price_base": 1403.31,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1604079628040-94301bb21b11",
            "active": True,
        },
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "SND-BAR-003",
            "name": "Barra de sonido 5.1",
            "description": "Barra de sonido 5.1 con subwoofer inalámbrico.",
            "price_final": 299.00,
            "price_base": 247.11,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b",
            "active": True,
        },

        # SMARTPHONES
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "PH-IP13-004",
            "name": "iPhone 13 128GB",
            "description": "Smartphone Apple 6.1'' 128GB.",
            "price_final": 799.00,
            "price_base": 660.33,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9",
            "active": True,
        },
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "PH-S23-005",
            "name": "Samsung Galaxy S23",
            "description": "Smartphone Samsung gama alta 256GB.",
            "price_final": 849.00,
            "price_base": 701.65,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1610945265078-7f3c8ec3df0d",
            "active": True,
        },
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "PH-XIA-006",
            "name": "Xiaomi 13 Lite",
            "description": "Smartphone calidad/precio, 128GB.",
            "price_final": 349.00,
            "price_base": 288.43,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1603899122634-2f24c0c4fd75",
            "active": True,
        },

        # PORTÁTILES
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "LT-MBA-007",
            "name": 'MacBook Air 13" M2',
            "description": "Portátil Apple M2, 8GB RAM, 256GB SSD.",
            "price_final": 1299.00,
            "price_base": 1073.55,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8",
            "active": True,
        },
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "LT-DEL-008",
            "name": "Dell XPS 13",
            "description": "Ultrabook 13'' pantalla InfinityEdge.",
            "price_final": 1199.00,
            "price_base": 991.74,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475",
            "active": True,
        },
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "LT-ASU-009",
            "name": "ASUS ZenBook 14",
            "description": "Portátil ligero 14'' con SSD 512GB.",
            "price_final": 899.00,
            "price_base": 742.15,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8",
            "active": True,
        },

        # GAMING
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "GM-PS5-010",
            "name": "PlayStation 5",
            "description": "Consola PS5 estándar, 825GB SSD.",
            "price_final": 549.00,
            "price_base": 453.72,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1606813907291-d86efa9b94a9",
            "active": True,
        },
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "GM-XBX-011",
            "name": "Xbox Series X",
            "description": "Consola gaming 4K, 1TB SSD.",
            "price_final": 499.00,
            "price_base": 412.40,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1621252179027-944cc673594a",
            "active": True,
        },
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "GM-NIN-012",
            "name": "Nintendo Switch OLED",
            "description": "Consola híbrida con pantalla OLED.",
            "price_final": 349.00,
            "price_base": 288.43,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1580237088170-e8e29b09b9a6",
            "active": True,
        },

        # HOGAR / PEQUEÑO ELECTRO
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "HM-VAC-013",
            "name": "Aspirador sin cable",
            "description": "Aspirador ciclónico sin cable, 60min autonomía.",
            "price_final": 199.00,
            "price_base": 164.46,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1581578731548-c64695cc6952",
            "active": True,
        },
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "HM-COF-014",
            "name": "Cafetera Espresso",
            "description": "Cafetera espresso automática con vaporizador.",
            "price_final": 249.00,
            "price_base": 205.79,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1447933601403-0c6688de566e",
            "active": True,
        },

        # WEARABLES
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "WR-APL-015",
            "name": "Apple Watch SE",
            "description": "Reloj inteligente Apple Watch SE GPS.",
            "price_final": 299.00,
            "price_base": 247.11,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1514405709054-d0cc78c9a09c",
            "active": True,
        },
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "WR-FIT-016",
            "name": "Pulsera fitness",
            "description": "Pulsera de actividad con medición de sueño.",
            "price_final": 59.00,
            "price_base": 48.76,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1519744792095-2f2205e87b6f",
            "active": True,
        },

        # AURICULARES
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "AU-ANC-017",
            "name": "Auriculares Bluetooth ANC",
            "description": "Auriculares circumaurales con cancelación activa.",
            "price_final": 199.00,
            "price_base": 164.46,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1519677100203-a0e668c92439",
            "active": True,
        },
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "AU-TWS-018",
            "name": "Auriculares True Wireless",
            "description": "Auriculares TWS con estuche de carga.",
            "price_final": 99.00,
            "price_base": 81.82,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1583394838336-acd977736f90",
            "active": True,
        },

        # MONITORES
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "MN-27-019",
            "name": 'Monitor 27" QHD',
            "description": "Monitor QHD 27'' 75Hz para oficina.",
            "price_final": 249.00,
            "price_base": 205.79,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8",
            "active": True,
        },
        {
            "organization_id": ORG_ID,
            "provider_id": PROVIDER_ID,
            "sku": "MN-34-020",
            "name": 'Monitor 34" UltraWide',
            "description": "Monitor panorámico 34'' UltraWide.",
            "price_final": 499.00,
            "price_base": 412.40,
            "vat_rate": 21,
            "currency": "EUR",
            "image_url": "https://images.unsplash.com/photo-1526498460520-4c246339dccb",
            "active": True,
        },
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
