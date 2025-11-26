# backend_core/services/audit_repository.py

from typing import List, Dict, Any, Optional

from backend_core.services.supabase_client import table


# ======================================================
# LOGS GENERALES
# ======================================================

def get_all_logs_for_operator(operator_id: str) -> List[Dict[str, Any]]:
    """
    Devuelve todos los logs relacionados con un operador.
    Asumimos campo operator_id y opcionalmente country_code, etc.
    """
    q = (
        table("ca_audit_logs")
        .select("*")
        .eq("operator_id", operator_id)
        .order("created_at", desc=True)
    )
    rows = q.execute()
    return rows or []


def get_log_details(log_id: str, operator_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    q = table("ca_audit_logs").select("*").eq("id", log_id)
    if operator_id:
        q = q.eq("operator_id", operator_id)
    rows = q.execute()
    if not rows:
        return None
    return rows[0]


# ======================================================
# LOGS DE ADJUDICACIÓN DETERMINISTA
# ======================================================

def get_adjudication_log(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Devuelve el último log de adjudicación para una sesión.
    Asumimos que se registra en ca_audit_logs con event_type = 'session_adjudicated'.
    """
    q = (
        table("ca_audit_logs")
        .select("*")
        .eq("session_id", session_id)
        .eq("event_type", "session_adjudicated")
        .order("created_at", desc=True)
    )
    rows = q.execute()
    if not rows:
        return None
    return rows[0]


# Compatibilidad con versiones anteriores (engine_monitor antiguo)
def list_audit_logs() -> List[Dict[str, Any]]:
    q = table("ca_audit_logs").select("*").order("created_at", desc=True)
    rows = q.execute()
    return rows or []
