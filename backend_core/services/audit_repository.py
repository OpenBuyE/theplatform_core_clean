"""
audit_repository.py
Auditoría completa del sistema Compra Abierta.

Funciones:
- log_event: registrar acciones del sistema
- fetch_logs: obtener logs para el panel
"""

from datetime import datetime
from typing import Optional, Dict, List

from .supabase_client import supabase

AUDIT_TABLE = "audit_logs"


class AuditRepository:

    # ---------------------------------------------------------
    # REGISTRAR EVENTO DE AUDITORÍA
    # ---------------------------------------------------------
    def log_event(
        self,
        action: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> None:

        entry = {
            "action": action,
            "session_id": session_id,
            "user_id": user_id,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }

        supabase.table(AUDIT_TABLE).insert(entry).execute()

    # ---------------------------------------------------------
    # OBTENER LOGS PARA EL PANEL
    # ---------------------------------------------------------
    def fetch_logs(
        self,
        limit: int = 300,
        session_id: Optional[str] = None,
        action: Optional[str] = None
    ) -> List[Dict]:

        query = supabase.table(AUDIT_TABLE).select("*")

        if session_id:
            query = query.eq("session_id", session_id)

        if action:
            query = query.eq("action", action)

        query = query.order("created_at", desc=True).limit(limit)

        response = query.execute()
        return response.data or []


# Instancia global
audit_repository = AuditRepository()

# Export “log_event” para mantener compatibilidad con el panel
log_event = audit_repository.log_event
fetch_logs = audit_repository.fetch_logs
