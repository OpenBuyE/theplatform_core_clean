# backend_core/services/product_repository_v2.py

from backend_core.services.supabase_client import table

PRODUCTS_TABLE = "products_v2"
CATEGORIES_TABLE = "categorias_v2"
OPERATORS_TABLE = "ca_operators"


# ===========================================================
# CATEGORIES
# ===========================================================

def list_categories():
    """
    Devuelve todas las categorías.

    Tabla categorias_v2 (supuesto):
      - id
      - categoria        → nombre legible
      - descripcion      → opcional
    """
    resp = (
        table(CATEGORIES_TABLE)
        .select("*")
        .order("categoria")
        .execute()
    )
    return resp.data or []


def get_category_by_id(category_id: str):
    if not category_id:
        return None

    resp = (
        table(CATEGORIES_TABLE)
        .select("*")
        .eq("id", category_id)
        .single()
        .execute()
    )
    return resp.data


def create_category(nombre: str, descripcion: str | None = None) -> bool:
    """
    Crea una categoría en categorias_v2.
    """
    data = {
        "categoria": nombre,
    }
    if descripcion is not None:
        data["descripcion"] = descripcion

    resp = table(CATEGORIES_TABLE).insert(data).execute()
    return resp.data is not None


def update_category(category_id: str, nombre: str | None = None, descripcion: str | None = None) -> bool:
    """
    Actualiza una categoría por id.
    Solo toca los campos que se pasan no nulos.
    """
    data: dict = {}
    if nombre is not None:
        data["categoria"] = nombre
    if descripcion is not None:
        data["descripcion"] = descripcion

    if not data:
        return True  # nada que actualizar

    resp = (
        table(CATEGORIES_TABLE)
        .update(data)
        .eq("id", category_id)
        .execute()
    )
    return resp.data is not None


def delete_category(category_id: str) -> bool:
    """
    Borra físicamente una categoría.
    """
    resp = (
        table(CATEGORIES_TABLE)
        .delete()
        .eq("id", category_id)
        .execute()
    )
    return resp is not None


# ===========================================================
# PRODUCTS — LISTADOS BÁSICOS
# ===========================================================

def list_products(limit: int = 100):
    """Lista productos (por defecto, últimos 100)."""
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data or []


def list_products_for_kpi(max_rows: int = 10000):
    """
    Lista productos sin filtros estrictos, para KPIs.
    Pensado para tablas pequeñas/medias.
    """
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .limit(max_rows)
        .execute()
    )
    return resp.data or []


def filter_products(
    category_id: str = None,
    min_price: float | None = None,
    max_price: float | None = None,
    search: str | None = None,
):
    """
    Filtro flexible:
      - category_id
      - rango de precio (price_final)
      - búsqueda por nombre (ilike)
    """
    q = table(PRODUCTS_TABLE).select("*")

    if category_id:
        q = q.eq("category_id", category_id)

    if search:
        pattern = f"%{search}%"
        q = q.ilike("name", pattern)

    if min_price is not None:
        q = q.gte("price_final", min_price)

    if max_price is not None:
        q = q.lte("price_final", max_price)

    resp = q.order("created_at", desc=True).execute()
    return resp.data or []


def get_product_by_id(product_id: str):
    """Devuelve un producto por id (PK = id)."""
    resp = (
        table(PRODUCTS_TABLE)
        .select("*")
        .eq("id", product_id)
        .single()
        .execute()
    )
    return resp.data


# Alias para compatibilidad
def get_product_v2(product_id: str):
    return get_product_by_id(product_id)


def create_product(data: dict) -> bool:
    """
    Inserta un producto completo en products_v2.
    """
    try:
        resp = table(PRODUCTS_TABLE).insert(data).execute()
        return resp.data is not None
    except Exception as e:
        print("ERROR create_product:", e)
        return False


# ===========================================================
# PROVIDERS (OPERATORS) — para Product Details PRO
# ===========================================================

def get_provider_by_id(provider_id: str):
    if not provider_id:
        return None

    resp = (
        table(OPERATORS_TABLE)
        .select("*")
        .eq("id", provider_id)
        .single()
        .execute()
    )
    return resp.data


# ===========================================================
# KPIs DE CATÁLOGO (para Product Catalog Pro)
# ===========================================================

def get_catalog_summary():
    """
    Devuelve un resumen global del catálogo:
      - total_products
      - total_categories
      - avg_price
      - products_by_category: {category_id|None: count}
    """
    products = list_products_for_kpi()
    categories = list_categories()

    total_products = len(products)
    category_ids = {p.get("category_id") for p in products if p.get("category_id")}
    total_categories = len(category_ids)

    prices = [float(p["price_final"]) for p in products if p.get("price_final") is not None]
    avg_price = sum(prices) / len(prices) if prices else None

    products_by_category: dict[str | None, int] = {}
    for p in products:
        cid = p.get("category_id")
        products_by_category[cid] = products_by_category.get(cid, 0) + 1

    # Map ids → nombres
    cat_map = {c["id"]: c.get("categoria") or c["id"] for c in categories}

    return {
        "total_products": total_products,
        "total_categories": total_categories,
        "avg_price": avg_price,
        "products_by_category": products_by_category,
        "category_name_map": cat_map,
    }


def get_category_stats():
    """
    Devuelve una lista de dicts por categoría:
      - category_id
      - category_name
      - product_count
      - avg_price
      - min_price
      - max_price
    Incluye una pseudo-categoría 'UNCATEGORIZED' si hay productos sin category_id.
    """
    products = list_products_for_kpi()
    categories = list_categories()
    cat_name_map = {c["id"]: c.get("categoria") or c["id"] for c in categories}

    buckets: dict[str, list[dict]] = {}

    for p in products:
        cid = p.get("category_id")
        key = cid if cid is not None else "UNCATEGORIZED"
        if key not in buckets:
            buckets[key] = []
        buckets[key].append(p)

    stats = []

    for key, plist in buckets.items():
        prices = [float(p["price_final"]) for p in plist if p.get("price_final") is not None]
        if prices:
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
        else:
            avg_price = min_price = max_price = None

        if key == "UNCATEGORIZED":
            name = "Sin categoría"
            category_id = None
        else:
            name = cat_name_map.get(key, key)
            category_id = key

        stats.append(
            {
                "category_id": category_id,
                "category_name": name,
                "product_count": len(plist),
                "avg_price": avg_price,
                "min_price": min_price,
                "max_price": max_price,
            }
        )

    # Orden: más productos primero
    stats.sort(key=lambda x: x["product_count"], reverse=True)
    return stats
