# backend_core/services/audit_repository.py

from datetime import datetime
from backend_core.services.supabase_client import table
from backend_core.services.operator_repository import ensure_country_filter


# ============================================================
# REGISTRO DE EVENTOS (LOG EVENT)
# ============================================================

def log_event(event_type, session_id=None, operator_id=None, metadata=None):
    """
    Crea un registro de auditoría.
    Compatible con todas las versiones previas.
    """
    record = {
        "event_type": event_type,
        "session_id": session_id,
        "operator_id": operator_id,
        "metadata": metadata or {},
        "created_at": datetime.utcnow().isoformat(),
    }

    res = table("ca_audit_logs").insert(record).execute()
    return res[0] if res else None


# ============================================================
# OBTENER TODOS LOS LOGS (ADMIN MASTER)
# ============================================================

def get_all_logs(limit=500):
    return (
        table("ca_audit_logs")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )


# ============================================================
# LOGS PARA OPERADOR (FILTRADO POR PAÍS)
# ============================================================

def get_all_logs_for_operator(operator):
    """
    Devuelve logs filtrados por países permitidos para el operador.
    """
    field, allowed = ensure_country_filter(operator)

    return (
        table("ca_audit_logs")
        .select("*")
        .in_(field, allowed)
        .order("created_at", desc=True)
        .execute()
    )


# ============================================================
# DETALLES DE UN LOG (LEGACY)
# ============================================================

def get_log_details(log_id):
    """
    Devuelve el contenido completo de un log.
    Necesario para compatibilidad con pantallas antiguas.
    """
    return (
        table("ca_audit_logs")
        .select("*")
        .eq("id", log_id)
        .single()
        .execute()
    )


# ============================================================
# LOGS POR SESIÓN
# ============================================================

def get_logs_for_session(session_id):
    return (
        table("ca_audit_logs")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", asc=True)
        .execute()
    )


# ============================================================
# LOGS POR TIPO DE EVENTO
# ============================================================

def get_logs_by_event_type(event_type):
    return (
        table("ca_audit_logs")
        .select("*")
        .eq("event_type", event_type)
        .order("created_at", desc=True)
        .execute()
    )


# ============================================================
# CONTAR LOGS (KPIs)
# ============================================================

def count_logs():
    return (
        table("ca_audit_logs")
        .select("id", count="exact")
        .execute()
    )
