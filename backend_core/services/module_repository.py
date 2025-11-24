# backend_core/services/module_repository.py

from __future__ import annotations
from typing import Optional, List, Dict, Any

from backend_core.services.supabase_client import table


MODULES_TABLE = "ca_session_modules"
SESSIONS_TABLE = "ca_sessions"


# ---------------------------------------------------------
# UTILIDADES PRINCIPALES
# ---------------------------------------------------------

def list_modules() -> List[Dict[str, Any]]:
    """
    Devuelve todos los módulos registrados en ca_session_modules.
    """
    resp = (
        table(MODULES_TABLE)
        .select("*")
        .order("module_code")
        .execute()
    )
    return resp.data or []


def get_module(module_code: str) -> Optional[Dict[str, Any]]:
    """
    Devuelve un módulo específico por su module_code.
    """
    resp = (
        table(MODULES_TABLE)
        .select("*")
        .eq("module_code", module_code)
        .single()
        .execute()
    )
    return resp.data or None


def get_active_modules() -> List[Dict[str, Any]]:
    """
    Devuelve solo los módulos activos.
    """
    resp = (
        table(MODULES_TABLE)
        .select("*")
        .eq("active", True)
        .order("module_code")
        .execute()
    )
    return resp.data or []


# ---------------------------------------------------------
# ASIGNACIÓN DE MÓDULO A UNA SESIÓN
# ---------------------------------------------------------

def assign_module_to_session(session_id: str, module_code: str) -> Dict[str, Any]:
    """
    Asigna un módulo a una sesión. Valida que el módulo exista.
    """
    module = get_module(module_code)
    if not module:
        raise ValueError(f"Module '{module_code}' no existe en ca_session_modules.")

    resp = (
        table(SESSIONS_TABLE)
        .update({"module_code": module_code})
        .eq("id", session_id)
        .execute()
    )

    if not resp.data:
        raise RuntimeError(f"Error asignando module_code '{module_code}' a session '{session_id}'.")

    return resp.data[0]


def get_session_module(session: Dict[str, Any]) -> Dict[str, Any]:
    """
    Devuelve el módulo completo asociado a una sesión.
    Si module_code no existe, retorna el módulo por defecto (A_DETERMINISTIC).
    """
    module_code = session.get("module_code") or "A_DETERMINISTIC"
    module = get_module(module_code)

    if not module:
        # Fallback total — no debería ocurrir si la tabla está bien configurada
        return get_module("A_DETERMINISTIC")

    return module

