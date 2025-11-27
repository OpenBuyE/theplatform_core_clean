# backend_core/services/provider_repository_v2.py

from datetime import datetime
from backend_core.services.supabase_client import table
from backend_core.services.operator_repository import ensure_country_filter


# ============================================================
# LISTAR PROVEEDORES (con filtro multi-país profesional)
# ============================================================

def list_providers(operator=None):
    """
    Devuelve la lista de proveedores.
    Si se pasa un operador autenticado, se aplica control por país,
    rol y permisos avanzados mediante ensure_country_filter().
    """
    if operator:
        field, countries = ensure_country_filter(operator)
        return (
            table("ca_providers")
            .select("*")
            .in_(field, countries)
            .order("created_at", asc=True)
            .execute()
        )

    return (
        table("ca_providers")
        .select("*")
        .order("created_at", asc=True)
        .execute()
    )


# ============================================================
# CREAR PROVEEDOR
# ============================================================

def create_provider(name: str, country: str, metadata: dict = None):
    """
    Registra un proveedor con país obligatorio y metadatos opcionales.
    """
    record = {
        "name": name,
        "country": country,
        "metadata": metadata or {},
        "created_at": datetime.utcnow().isoformat(),
    }

    result = table("ca_providers").insert(record).execute()
    return result[0]["id"]


# ============================================================
# OBTENER PROVEEDOR POR ID
# ============================================================

def get_provider(provider_id: str):
    """
    Devuelve un proveedor concreto por su ID.
    """
    return (
        table("ca_providers")
        .select("*")
        .eq("id", provider_id)
        .single()
        .execute()
    )


# ============================================================
# ACTUALIZAR PROVEEDOR
# ============================================================

def update_provider(provider_id: str, data: dict):
    """
    Actualiza campos del proveedor.
    `data` es un dict con los campos a modificar.
    """
    return (
        table("ca_providers")
        .update(data)
        .eq("id", provider_id)
        .execute()
    )


# ============================================================
# ELIMINAR PROVEEDOR
# ============================================================

def delete_provider(provider_id: str):
    """
    Eliminación simple del proveedor.
    """
    return (
        table("ca_providers")
        .delete()
        .eq("id", provider_id)
        .execute()
    )
