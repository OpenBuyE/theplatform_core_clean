import typing as t
from backend_core.services.supabase_client import table
from backend_core.services.operator_repository import (
    get_operator_allowed_countries,
    ensure_country_filter,
)

# =========================================================
# HELPERS INTERNOS
# =========================================================

def _safe_data(resp):
    """Compatibilidad con diferentes formatos del wrapper Supabase REST."""
    if hasattr(resp, "data"):
        return resp.data
    return resp.get("data")


# =========================================================
# PRODUCTOS — CRUD + FILTROS MULTIPAÍS
# =========================================================

def list_products_v2(operator_id: str) -> t.List[dict]:
    """
    Lista todos los productos visibles por el operador.
    """
    allowed = get_operator_allowed_countries(operator_id)

    qb = table("products_v2").select("*")
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_data(resp) or []


def get_product_v2(product_id: str) -> t.Optional[dict]:
    """
    Devuelve un producto por ID (sin filtro por país — detalle).
    """
    resp = (
        table("products_v2")
        .select("*")
        .eq("id", product_id)
        .single()
        .execute()
    )
    return _safe_data(resp)


def create_product(data: dict) -> dict:
    """
    Crea un producto nuevo.
    data debe contener:
        name, description, price_base, vat_rate, price_final,
        sku, category_id, provider_id, currency, country_code
    """
    resp = table("products_v2").insert(data).execute()
    return _safe_data(resp)


def update_product(product_id: str, updates: dict) -> dict:
    """
    Actualiza los campos indicados para un producto.
    """
    resp = (
        table("products_v2")
        .update(updates)
        .eq("id", product_id)
        .execute()
    )
    return _safe_data(resp)


# =========================================================
# FILTROS AVANZADOS (CATÁLOGO PRO)
# =========================================================

def filter_products(
    operator_id: str,
    category_id: t.Optional[str] = None,
    provider_id: t.Optional[str] = None,
    min_price: t.Optional[float] = None,
    max_price: t.Optional[float] = None,
    text: t.Optional[str] = None,
) -> t.List[dict]:
    """
    Filtro completo usado en Product Catalog Pro.
    """
    allowed = get_operator_allowed_countries(operator_id)

    qb = table("products_v2").select("*")
    qb = ensure_country_filter(qb, allowed)

    if category_id and category_id != "ALL":
        qb = qb.eq("category_id", category_id)

    if provider_id and provider_id != "ALL":
        qb = qb.eq("provider_id", provider_id)

    if min_price is not None:
        qb = qb.gte("price_final", min_price)

    if max_price is not None:
        qb = qb.lte("price_final", max_price)

    if text:
        pattern = f"%{text}%"
        qb = qb.ilike("name", pattern)

    resp = qb.execute()
    return _safe_data(resp) or []


# =========================================================
# CATEGORÍAS — CRUD
# =========================================================

def list_categories(operator_id: str) -> t.List[dict]:
    allowed = get_operator_allowed_countries(operator_id)

    qb = table("categorias_v2").select("*")
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_data(resp) or []


def get_category_by_id(category_id: str) -> t.Optional[dict]:
    resp = (
        table("categorias_v2")
        .select("*")
        .eq("id", category_id)
        .single()
        .execute()
    )
    return _safe_data(resp)


def create_category(name: str, description: str, country_code: str) -> dict:
    payload = {
        "name": name,
        "description": description,
        "country_code": country_code,
    }

    resp = table("categorias_v2").insert(payload).execute()
    return _safe_data(resp)


def update_category(category_id: str, updates: dict) -> dict:
    resp = (
        table("categorias_v2")
        .update(updates)
        .eq("id", category_id)
        .execute()
    )
    return _safe_data(resp)


def delete_category(category_id: str) -> dict:
    resp = (
        table("categorias_v2")
        .delete()
        .eq("id", category_id)
        .execute()
    )
    return _safe_data(resp)


# =========================================================
# PROVIDERS — GET BÁSICO
# =========================================================

def list_providers(operator_id: str) -> t.List[dict]:
    allowed = get_operator_allowed_countries(operator_id)

    qb = table("providers_v2").select("*")
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_data(resp) or []


def get_provider_by_id(provider_id: str) -> t.Optional[dict]:
    resp = (
        table("providers_v2")
        .select("*")
        .eq("id", provider_id)
        .single()
        .execute()
    )
    return _safe_data(resp)
