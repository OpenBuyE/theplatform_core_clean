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

    Asumimos que la tabla categorias_v2 tiene al menos:
      - id
      - categoria (nombre legible)
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
    Campos típicos:
      - categoria      → nombre
      - descripcion    → texto opcional
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
    (Si en el futuro quieres soft-delete, aquí se cambia por update active=false).
    """
    resp = (
        table(CATEGORIES_TABLE)
        .delete()
        .eq("id", category_id)
        .execute()
    )
    # En PostgREST, delete devuelve [] si ok.
    return resp is not None


# ===========================================================
# PRODUCTS
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


def filter_products(category_id: str = None, min_price: float | None = None,
                    max_price: float | None = None, search: str | None = None):
    """
    Filtro flexible:
      - category_id
      - rango de precio
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


# Alias para compatibilidad con código que usa get_product_v2
def get_product_v2(product_id: str):
    return get_product_by_id(product_id)


def create_product(data: dict) -> bool:
    """
    Inserta un producto completo en products_v2.

    Data debe incluir como mínimo:
      - id
      - organization_id
      - provider_id (puede ser None)
      - category_id
      - name
      - price_final
    Y opcionalmente:
      - sku
      - description
      - price_base
      - vat_rate
      - currency
      - image_url
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
