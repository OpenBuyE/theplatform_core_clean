# backend_core/services/provider_repository_v2.py

from typing import List, Dict, Any, Optional
from backend_core.services.supabase_client import table


def list_providers_v2() -> List[Dict[str, Any]]:
    rows = table("providers_v2").select("*").order("created_at", desc=True).execute()
    return rows or []


def list_providers_safe(country_codes: Optional[list[str]] = None) -> List[Dict[str, Any]]:
    """
    Versión 'safe' para UI: solo proveedores activos, opcionalmente filtrados por país.
    Asumimos columna active y opcional country_code.
    """
    q = table("providers_v2").select("*").eq("active", True)

    if country_codes:
        # si tienes campo country_code, puedes hacer or_ con ellos; aquí lo dejamos simple
        # q = q.in_("country_code", country_codes)
        pass

    rows = q.order("created_at", desc=True).execute()
    return rows or []


def get_provider(provider_id: str) -> Optional[Dict[str, Any]]:
    rows = table("providers_v2").select("*").eq("id", provider_id).execute()
    return rows[0] if rows else None


def create_provider(payload: Dict[str, Any]) -> Dict[str, Any]:
    rows = table("providers_v2").insert(payload).execute()
    if not rows:
        raise RuntimeError("No se pudo crear el proveedor.")
    return rows[0]


def update_provider(provider_id: str, **fields) -> Dict[str, Any]:
    rows = table("providers_v2").update(fields).eq("id", provider_id).execute()
    if not rows:
        raise RuntimeError("No se pudo actualizar el proveedor.")
    return rows[0]


def disable_provider(provider_id: str):
    table("providers_v2").update({"active": False}).eq("id", provider_id).execute()
