# backend_core/services/provider_repository_v2.py

from datetime import datetime
from uuid import uuid4

from backend_core.services.supabase_client import table
from backend_core.services.operator_repository import ensure_country_filter


# ============================================================
# LISTAR PROVEEDORES (COMPLETO)
# ============================================================

def list_providers():
    """
    Lista todos los proveedores sin filtros.
    Compatible con versiones antiguas.
    """
    return table("ca_providers").select("*").order("name", asc=True).execute()


def list_providers_safe(operator):
    """
    Lista proveedores filtrados según los países permitidos al operador.
    """
    field, allowed = ensure_country_filter(operator)

    return (
        table("ca_providers")
        .select("*")
        .in_(field, allowed)
        .order("name", asc=True)
        .execute()
    )


# ============================================================
# OBTENER PROVEEDOR
# ============================================================

def get_provider(provider_id):
    """
    Devuelve un proveedor concreto.
    """
    return (
        table("ca_providers")
        .select("*")
        .eq("id", provider_id)
        .single()
        .execute()
    )


# ============================================================
# CREAR PROVEEDOR
# ============================================================

def create_provider(data: dict):
    """
    Crea un proveedor nuevo.
    Campos esperados:
    - name
    - country_code
    - contact_email
    - phone
    - address
    - logo_url (opcional)
    - metadata (dict)
    """

    provider_id = str(uuid4())

    record = {
        "id": provider_id,
        "name": data.get("name"),
        "country_code": data.get("country_code", "ES"),
        "contact_email": data.get("contact_email"),
        "phone": data.get("phone"),
        "address": data.get("address"),
        "logo_url": data.get("logo_url"),
        "metadata": data.get("metadata") or {},
        "active": True,
        "created_at": datetime.utcnow().isoformat(),
    }

    res = table("ca_providers").insert(record).execute()
    return provider_id if res else None


# ============================================================
# ACTUALIZAR PROVEEDOR
# ============================================================

def update_provider(provider_id: str, data: dict):
    """
    Actualiza campos del proveedor.
    """
    return (
        table("ca_providers")
        .update(data)
        .eq("id", provider_id)
        .execute()
    )


# ============================================================
# ELIMINAR / DESACTIVAR PROVEEDOR
# ============================================================

def delete_provider(provider_id: str, hard=False):
    """
    hard=False → desactiva el proveedor
    hard=True  → elimina de la base
    """
    if hard:
        return table("ca_providers").delete().eq("id", provider_id).execute()

    return (
        table("ca_providers")
        .update({"active": False})
        .eq("id", provider_id)
        .execute()
    )


# ============================================================
# LISTAR PROVEEDORES POR PAÍS
# ============================================================

def list_providers_by_country(country_code: str):
    return (
        table("ca_providers")
        .select("*")
        .eq("country_code", country_code)
        .order("name", asc=True)
        .execute()
    )


# ============================================================
# CONTAR PROVEEDORES (para KPIs)
# ============================================================

def count_providers():
    """
    Devuelve {"count": X}
    """
    return (
        table("ca_providers")
        .select("id", count="exact")
        .execute()
    )
