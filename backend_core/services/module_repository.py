# backend_core/services/module_repository.py

from typing import List, Optional, Dict, Any

from backend_core.services.supabase_client import table

MODULES_TABLE = "ca_modules"
SESSION_MODULES_TABLE = "ca_session_modules"


# =======================================================
# LISTAR TODOS LOS MÓDULOS DEFINIDOS
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
# OBTENER MÓDULO POR ID
# =======================================================
def get_module_by_id(module_id: str) -> Optional[Dict[str, Any]]:
    resp = (
        table(MODULES_TABLE)
        .select("*")
        .eq("id", module_id)
        .single()
        .execute()
    )
    return resp.data


# =======================================================
# OBTENER MÓDULO DE UNA SESIÓN
# =======================================================
def get_module_for_session(session_id: str) -> Optional[Dict[str, Any]]:
    # 1. Obtener la relación sesión-módulo
    rel_resp = (
        table(SESSION_MODULES_TABLE)
        .select("*")
        .eq("session_id", session_id)
        .single()
        .execute()
    )

    rel = rel_resp.data
    if not rel:
        return None

    # 2. Cargar el módulo
    return get_module_by_id(rel["module_id"])


# =======================================================
# ASIGNAR MÓDULO A UNA SESIÓN
# =======================================================
def assign_module_to_session(session_id: str, module_id: str) -> None:
    # Ver si ya existe relación
    existing = (
        table(SESSION_MODULES_TABLE)
        .select("*")
        .eq("session_id", session_id)
        .execute()
        .data
    )

    if existing:
        # Actualizar módulo asignado
        (
            table(SESSION_MODULES_TABLE)
            .update({"module_id": module_id})
            .eq("session_id", session_id)
            .execute()
        )
        return

    # Insertar nueva relación
    (
        table(SESSION_MODULES_TABLE)
        .insert(
            {
                "session_id": session_id,
                "module_id": module_id,
            }
        )
        .execute()
    )


# =======================================================
# DESACTIVAR MÓDULO
# =======================================================
def deactivate_module(module_id: str) -> None:
    (
        table(MODULES_TABLE)
        .update({"is_active": False})
        .eq("id", module_id)
        .execute()
    )
