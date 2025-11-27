# backend_core/services/audit_repository.py

import uuid
from datetime import datetime
from backend_core.services.supabase_client import table


# ======================================================================
# REGISTRO DE AUDITORÍA
# ======================================================================

def log_event(event_type: str, session_id: str = None, details: dict = None, operator_id: str = None):
    """
    Guarda un evento en la tabla ca_audit_logs.
    Compatible con TODAS las vistas que llaman log_event().
    """

    payload = {
        "id": str(uuid.uuid4()),
        "event_type": event_type,
        "session_id": session_id,
        "operator_id": operator_id,
        "details": details or {},
        "created_at": datetime.utcnow().isoformat(),
    }

    table("ca_audit_logs").insert(payload).execute()

    return True


# ======================================================================
# OBTENER LOGS POR OPERADOR
# ======================================================================

def get_all_logs_for_operator(operator_id: str):
    """
    Devuelve todos los eventos de auditoría generados por un operador.
    Usado por Admin Logs.
    """
    result = (
        table("ca_audit_logs")
        .select("*")
        .eq("operator_id", operator_id)
        .order("created_at", desc=True)
        .execute()
    )

    return result or []


# ======================================================================
# LOGS FILTRADOS POR SESIÓN
# ======================================================================

def get_adjudication_log(session_id: str):
    """
    Obtiene logs de adjudicación para una sesión.
    Necesario para Session History, Session Chains, etc.
    """
    result = (
        table("ca_audit_logs")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .execute()
    )

    return result or []


# ======================================================================
# TODOS LOS LOGS (ADMIN MASTER)
# ======================================================================

def get_all_logs(limit: int = 200):
    """
    Devuelve los logs más recientes del sistema.
    Usado por Engine Monitor y Admin Engine.
    """

    result = (
        table("ca_audit_logs")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    return result or []
