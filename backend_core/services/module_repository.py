# backend_core/services/module_repository.py

from typing import List, Dict, Any
from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event


MODULES_TABLE = "ca_modules"
MODULE_SESSIONS_TABLE = "ca_module_sessions"


# =======================================================
# LIST ALL MODULES
# =======================================================

def list_all_modules() -> List[Dict[str, Any]]:
    resp = (
        table(MODULES_TABLE)
        .select("*")
        .eq("is_active", True)
        .execute()
    )
    return resp.data or []


# =======================================================
# ASSIGN MODULE TO SESSION
# =======================================================

def assign_module(session_id: str, module_id: str):
    """
    Crea el registro session → module en ca_module_sessions.
    """
    _ = (
        table(MODULE_SESSIONS_TABLE)
        .insert(
            {
                "session_id": session_id,
                "module_id": module_id,
            }
        )
        .execute()
    )

    log_event("module_assigned", {"session_id": session_id, "module_id": module_id})


# =======================================================
# GET MODULE FOR SESSION
# =======================================================

def get_module_for_session(session_id: str) -> Dict[str, Any]:
    """
    Devuelve el módulo asignado a una sesión.
    """

    # primero obtener el registro de asignación
    rel = (
        table(MODULE_SESSIONS_TABLE)
        .select("*")
        .eq("session_id", session_id)
        .single()
        .execute()
    ).data

    if not rel:
        return None

    module_id = rel["module_id"]

    # ahora obtener el módulo real
    module = (
        table(MODULES_TABLE)
        .select("*")
        .eq("id", module_id)
        .single()
        .execute()
    ).data

    return module


# =======================================================
# MARK MODULE AWARDED (solo módulo A)
# =======================================================

def mark_module_awarded(session_id: str):
    """
    Marca que el módulo ha tenido adjudicación (solo Módulo A).
    """
    rel = (
        table(MODULE_SESSIONS_TABLE)
        .select("*")
        .eq("session_id", session_id)
        .single()
        .execute()
    ).data

    if not rel:
        return

    _ = (
        table(MODULE_SESSIONS_TABLE)
        .update({"awarded": True})
        .eq("session_id", session_id)
        .execute()
    )

    log_event("module_awarded", {"session_id": session_id})


# =======================================================
# LIST MODULE ASSIGNMENTS (debug)
# =======================================================

def list_session_modules() -> List[Dict[str, Any]]:
    resp = table(MODULE_SESSIONS_TABLE).select("*").execute()
    return resp.data or []
