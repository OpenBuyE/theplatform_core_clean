# backend_core/services/audit_repository.py

from datetime import datetime
from backend_core.services.supabase_client import table
from backend_core.services.operator_repository import ensure_country_filter


# ============================================================
# REGISTRO DE EVENTOS
# ============================================================

def log_event(event_type, session_id=None, operator_id=None, metadata=None):
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
# CONSULTAS GENERALES
# ============================================================

def get_all_logs(limit=500):
    return (
        table("ca_audit_logs")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )


def get_all_logs_for_operator(operator, limit=500):
    field, countries = ensure_country_filter(operator)
    return (
        table("ca_audit_logs")
        .select("*")
        .in_(field, countries)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )


def get_logs_for_session(session_id: str):
    return (
        table("ca_audit_logs")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", asc=True)
        .execute()
    )


def get_logs_by_event_type(event_type: str):
    return (
        table("ca_audit_logs")
        .select("*")
        .eq("event_type", event_type)
        .order("created_at", desc=True)
        .execute()
    )


def get_log_details(log_id: str):
    return (
        table("ca_audit_logs")
        .select("*")
        .eq("id", log_id)
        .single()
        .execute()
    )


def get_adjudication_log(session_id: str):
    """
    Último log de adjudicación para una sesión.
    Usado por Session Chains / Session History.
    """
    return (
        table("ca_audit_logs")
        .select("*")
        .eq("session_id", session_id)
        .eq("event_type", "session_adjudicated")
        .order("created_at", desc=True)
        .limit(1)
        .single()
        .execute()
    )


def count_logs():
    return table("ca_audit_logs").select("id", count="exact").execute()
