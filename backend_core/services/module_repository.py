# backend_core/services/module_repository.py

from datetime import datetime
from backend_core.services.supabase_client import table


# ============================================================
# LISTAR MÓDULOS
# ============================================================

def list_all_modules():
    return (
        table("ca_modules")
        .select("*")
        .order("module_code", asc=True)
        .execute()
    )


# ============================================================
# OBTENER MÓDULO
# ============================================================

def get_module(module_id: str):
    return (
        table("ca_modules")
        .select("*")
        .eq("id", module_id)
        .single()
        .execute()
    )


# ============================================================
# ASIGNAR MÓDULO A SESIÓN
# ============================================================

def assign_module_to_session(session_id: str, module_id: str):
    data = {
        "session_id": session_id,
        "module_id": module_id,
        "created_at": datetime.utcnow().isoformat(),
    }
    res = table("ca_session_modules").insert(data).execute()
    return res[0] if res else None


# ============================================================
# OBTENER MÓDULO PARA SESIÓN
# ============================================================

def get_module_for_session(session_id: str):
    """
    Devuelve el módulo asociado a una sesión.
    """
    link = (
        table("ca_session_modules")
        .select("*")
        .eq("session_id", session_id)
        .single()
        .execute()
    )

    if not link:
        return None

    module = (
        table("ca_modules")
        .select("*")
        .eq("id", link["module_id"])
        .single()
        .execute()
    )
    return module


# ============================================================
# SESSION SERIES (usado en Admin Series)
# ============================================================

def list_session_series():
    """
    Lista todas las series operativas de sesiones.
    """
    return (
        table("ca_session_series")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
