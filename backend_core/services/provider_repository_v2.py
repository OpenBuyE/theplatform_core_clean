# backend_core/services/provider_repository_v2.py

from backend_core.services.supabase_client import table
import uuid
from datetime import datetime

PROVIDERS_TABLE = "providers_v2"

# ---------------------------------------------------------
# LISTAR PROVEEDORES
# ---------------------------------------------------------
def list_providers():
    resp = (
        table(PROVIDERS_TABLE)
        .select("*")
        .order("name")
        .execute()
    )
    return resp.data or []

# alias seguro (por compatibilidad con product_creator_pro)
def list_providers_safe():
    return list_providers()

# ---------------------------------------------------------
# OBTENER UN PROVEEDOR POR ID
# ---------------------------------------------------------
def get_provider_by_id(provider_id: str):
    resp = (
        table(PROVIDERS_TABLE)
        .select("*")
        .eq("id", provider_id)
        .single()
        .execute()
    )
    return resp.data

# ---------------------------------------------------------
# CREAR NUEVO PROVEEDOR
# ---------------------------------------------------------
def create_provider(name: str, contact_email: str = None, phone: str = None, address: str = None):
    provider_id = str(uuid.uuid4())

    data = {
        "id": provider_id,
        "name": name,
        "contact_email": contact_email,
        "phone": phone,
        "address": address,
        "created_at": datetime.utcnow().isoformat(),
        "is_active": True
    }

    resp = table(PROVIDERS_TABLE).insert(data).execute()
    return resp.data

# ---------------------------------------------------------
# ACTUALIZAR PROVEEDOR
# ---------------------------------------------------------
def update_provider(provider_id: str, name=None, contact_email=None, phone=None, address=None, is_active=None):
    update_data = {}

    if name is not None:
        update_data["name"] = name
    if contact_email is not None:
        update_data["contact_email"] = contact_email
    if phone is not None:
        update_data["phone"] = phone
    if address is not None:
        update_data["address"] = address
    if is_active is not None:
        update_data["is_active"] = is_active

    resp = (
        table(PROVIDERS_TABLE)
        .update(update_data)
        .eq("id", provider_id)
        .execute()
    )

    return resp.data

# ---------------------------------------------------------
# BORRAR PROVEEDOR (soft delete = desactivar)
# ---------------------------------------------------------
def deactivate_provider(provider_id: str):
    resp = (
        table(PROVIDERS_TABLE)
        .update({"is_active": False})
        .eq("id", provider_id)
        .execute()
    )
    return resp.data
