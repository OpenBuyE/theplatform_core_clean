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
    """Compatibilidad con diferentes formatos del wrapper REST."""
    if hasattr(resp, "data"):
        return resp.data
    return resp.get("data")


# =========================================================
# PROVIDERS — CRUD + MULTIPAÍS
# =========================================================

def list_providers(operator_id: str) -> t.List[dict]:
    """
    Lista todos los proveedores visibles por el operador,
    respetando los países asignados.
    """
    allowed = get_operator_allowed_countries(operator_id)

    qb = table("providers_v2").select("*")
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_data(resp) or []


def get_provider_by_id(provider_id: str) -> t.Optional[dict]:
    """
    Devuelve un proveedor por ID.
    (Acceso sin filtro porque es detalle directo).
    """
    resp = (
        table("providers_v2")
        .select("*")
        .eq("id", provider_id)
        .single()
        .execute()
    )
    return _safe_data(resp)


def create_provider(data: dict) -> dict:
    """
    Crea un proveedor nuevo.
    data debe incluir:
        name, email, phone, organization_id, country_code, active
    Opcional: logo_url, reputación, shipping_template
    """
    resp = table("providers_v2").insert(data).execute()
    return _safe_data(resp)


def update_provider(provider_id: str, updates: dict) -> dict:
    """
    Actualiza proveedor.
    """
    resp = (
        table("providers_v2")
        .update(updates)
        .eq("id", provider_id)
        .execute()
    )
    return _safe_data(resp)


def disable_provider(provider_id: str) -> dict:
    """
    Desactiva proveedor sin eliminarlo.
    """
    resp = (
        table("providers_v2")
        .update({"active": False})
        .eq("id", provider_id)
        .execute()
    )
    return _safe_data(resp)


def delete_provider(provider_id: str) -> dict:
    """
    Elimina proveedor definitivamente.
    (Se recomienda desactivar en producción.)
    """
    resp = (
        table("providers_v2")
        .delete()
        .eq("id", provider_id)
        .execute()
    )
    return _safe_data(resp)

