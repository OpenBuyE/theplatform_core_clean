from datetime import datetime
from backend_core.services.supabase_client import table


# ===========================================================
# 🔹 Registrar evento (estándar)
# ===========================================================

def log_event(
    event_type: str,
    operator_id: str = None,
    session_id: str = None,
    extra: dict = None
):
    """
    Registra cualquier evento en audit_log.
    """
    payload = {
        "event_type": event_type,
        "operator_id": operator_id,
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "extra": extra or {},
    }

    return table("audit_log").insert(payload).execute()


# ===========================================================
# 🔹 Obtener logs de un operador concreto
# ===========================================================

def get_all_logs_for_operator(operator_id: str):
    """
    Devuelve todos los logs filtrados por operador.
    """
    return (
        table("audit_log")
        .select("*")
        .eq("operator_id", operator_id)
        .order("timestamp", desc=True)
        .execute()
    )


# ===========================================================
# 🔹 Obtener detalles específicos de un log (legacy)
# ===========================================================

def get_log_details(log_id: str):
    """
    Devuelve un único registro de log.
    """
    return (
        table("audit_log")
        .select("*")
        .eq("id", log_id)
        .maybe_single()
        .execute()
    )


# ===========================================================
# 🔹 UTILIDAD PEDIDA POR ENGINE MONITOR
# ===========================================================

def list_audit_logs(limit: int = 200):
    """
    Devuelve lista de audit logs recientes.
    Engine Monitor depende de esta función.
    """
    return (
        table("audit_log")
        .select("*")
        .order("timestamp", desc=True)
        .limit(limit)
        .execute()
    )
