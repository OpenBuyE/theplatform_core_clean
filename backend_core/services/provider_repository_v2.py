# backend_core/services/provider_repository_v2.py
# =======================================================
# PROVIDER REPOSITORY V2 — CRUD Completo
# =======================================================

from backend_core.services.supabase_client import table

PROVIDERS_TABLE = "providers_v2"
ORG_ID = "11111111-1111-1111-1111-111111111111"


# -------------------------------------------------------
# LISTAR TODOS LOS PROVEEDORES
# -------------------------------------------------------
def list_providers():
    resp = (
        table(PROVIDERS_TABLE)
        .select("*")
        .eq("organization_id", ORG_ID)
        .order("name")
        .execute()
    )
    return resp.data or []


# Versión segura utilizada en Product Creator
def list_providers_safe():
    try:
        return list_providers()
    except:
        return []


# -------------------------------------------------------
# OBTENER UN PROVEEDOR POR ID
# -------------------------------------------------------
def get_provider(provider_id: str):
    resp = (
        table(PROVIDERS_TABLE)
        .select("*")
        .eq("id", provider_id)
        .single()
        .execute()
    )
    return resp.data


# -------------------------------------------------------
# CREAR PROVEEDOR
# -------------------------------------------------------
def create_provider(data: dict):
    resp = table(PROVIDERS_TABLE).insert(data).execute()
    return resp.data


# -------------------------------------------------------
# ACTUALIZAR PROVEEDOR
# -------------------------------------------------------
def update_provider(provider_id: str, data: dict):
    resp = (
        table(PROVIDERS_TABLE)
        .update(data)
        .eq("id", provider_id)
        .execute()
    )
    return resp.data


# -------------------------------------------------------
# ELIMINAR PROVEEDOR
# -------------------------------------------------------
def delete_provider(provider_id: str):
    resp = (
        table(PROVIDERS_TABLE)
        .delete()
        .eq("id", provider_id)
        .execute()
    )
    return resp.data
