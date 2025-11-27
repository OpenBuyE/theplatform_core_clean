# backend_core/services/module_repository.py

from backend_core.services.supabase_client import table


# ======================================================
# LISTA DE MÓDULOS DISPONIBLES
# ======================================================

def list_modules():
    return (
        table("ca_modules")
        .select("*")
        .order("created_at", asc=True)
        .execute()
    )


# ======================================================
# ASIGNAR MÓDULO A SESIÓN
# ======================================================

def assign_module(session_id: str, module_id: str):
    """
    Asigna un módulo específico a una sesión.
    """
    return (
        table("ca_sessions")
        .update({"module_id": module_id})
        .eq("id", session_id)
        .execute()
    )


# ======================================================
# MÓDULO DE SESIÓN
# ======================================================

def get_module_for_session(session_id: str):
    sess = (
        table("ca_sessions")
        .select("module_id")
        .eq("id", session_id)
        .single()
        .execute()
    )

    if not sess or not sess.get("module_id"):
        return None

    module_id = sess["module_id"]

    return (
        table("ca_modules")
        .select("*")
        .eq("id", module_id)
        .single()
        .execute()
    )


# ======================================================
# LISTAR MÓDULOS ASOCIADOS A UNA SERIE
# ======================================================

def list_session_modules(series_id: str):
    """
    Para Admin Series.
    Lista todos los módulos asociados a una sesión dentro de una serie.
    """
    return (
        table("ca_session_modules")
        .select("*")
        .eq("series_id", series_id)
        .order("created_at", asc=True)
        .execute()
    )
