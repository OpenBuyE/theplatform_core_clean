# backend_core/services/audit_repository.py

from __future__ import annotations
from datetime import datetime
from typing import Any, Optional

from backend_core.services.supabase_client import table

AUDIT_TABLE = "ca_audit_logs"


# ============================================================
#  LOG_EVENT — función principal usada por TODO el backend
# ============================================================

def log_event(
    action: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    """
    Inserta un evento en la tabla de auditoría ca_audit_logs.
    Es la función estándar utilizada en:
      - session_engine
      - adjudicator_engine
      - contract_engine
      - wallet_orchestrator
      - fintech_routes
      - dashboard
      - API internal
    """

    data = {
        "action": action,
        "session_id": session_id,
        "user_id": user_id,
        "metadata": metadata or {},
        "created_at": datetime.utcnow().isoformat(),
    }

    r = table(AUDIT_TABLE).insert(data).execute()

    # si Supabase devuelve error → raise
    if hasattr(r, "error") and r.error:
        raise RuntimeError(f"Audit log insert failed: {r.error}")


# ============================================================
#  GET_LOGS — utilitario para panel de auditoría
# ============================================================

def get_logs(limit: int = 200):
    """
    Obtiene los últimos eventos de auditoría.
    """
    resp = (
        table(AUDIT_TABLE)
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data or []
