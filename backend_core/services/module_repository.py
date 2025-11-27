# backend_core/services/module_repository.py

from backend_core.services.supabase_client import table

# ======================================================
# 📌 LISTAR TODOS LOS MÓDULOS DEL SISTEMA
# ======================================================

def list_all_modules():
    return (
        table("session_modules")
        .select("*")
        .order("module_code", desc=False)
        .execute()
    )


# ======================================================
# 📌 ASIGNAR MÓDULO A SESIÓN (alias moderno)
# ======================================================

def assign_module_to_session(session_id: str, module_id: str):
    return (
        table("session_module_links")
        .insert({
            "session_id": session_id,
            "module_id": module_id
        })
        .execute()
    )


# 🔄 COMPATIBILIDAD: nombre antiguo usado por algunas vistas
def assign_module(session_id: str, module_id: str):
    return assign_module_to_session(session_id, module_id)


# ======================================================
# 📌 OBTENER MÓDULO PARA UNA SESIÓN
# ======================================================

def get_module_for_session(session_id: str):
    result = (
        table("session_module_links")
        .select("module_id, session_modules(*)")
        .eq("session_id", session_id)
        .single()
        .execute()
    )
    return result.get("session_modules") if result else None


# ======================================================
# 📌 SERIES (Session Chains)
# ======================================================

def list_session_series():
    return (
        table("session_series")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )


def list_session_modules(series_id: str):
    return (
        table("session_series_modules")
        .select("*")
        .eq("series_id", series_id)
        .order("order_index", desc=False)
        .execute()
    )


# 🔄 COMPATIBILIDAD: función que esperan algunas vistas
def create_session_series(data: dict):
    return table("session_series").insert(data).execute()
