from datetime import datetime
from backend_core.services.supabase_client import table


# ===========================================================
# 🔹 Registrar evento estándar
# ===========================================================

def log_event(
    event_type: str,
    operator_id: str = None,
    session_id: str = None,
    extra: dict = None
):
    payload = {
        "event_type": event_type,
        "operator_id": operator_id,
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "extra": extra or {},
    }
    return table("audit_log").insert(payload).execute()


# ===========================================================
# 🔹 Obtener logs por operador
# ===========================================================

def get_all_logs_for_operator(operator_id: str):
    return (
        table("audit_log")
        .select("*")
        .eq("operator_id", operator_id)
        .order("timestamp", desc=True)
        .execute()
    )


# ===========================================================
# 🔹 Obtener detalles de un log concreto
# ===========================================================

def get_log_details(log_id: str):
    return (
        table("audit_log")
        .select("*")
        .eq("id", log_id)
        .maybe_single()
        .execute()
    )


# ===========================================================
# 🔹 Obtener lista de audit logs recientes (Engine Monitor)
# ===========================================================

def list_audit_logs(limit: int = 200):
    return (
        table("audit_log")
        .select("*")
        .order("timestamp", desc=True)
        .limit(limit)
        .execute()
    )


# ===========================================================
# 🔹 FUNCIÓN QUE FALTABA (legacy)
# get_adjudication_log(session_id)
# ===========================================================

def get_adjudication_log(session_id: str):
    """
    Devuelve todos los eventos de adjudicación para una sesión.
    Muchos módulos antiguos (Session Chains, History) dependen de esto.
    """
    return (
        table("audit_log")
        .select("*")
        .eq("session_id", session_id)
        .eq("event_type", "session_adjudicated")
        .order("timestamp", desc=True)
        .execute()
    )
