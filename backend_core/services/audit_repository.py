"""
audit_repository.py
Sistema de auditoría estable usando la tabla ca_audit_logs.

Esquema esperado:
---------------------------------------------------------
id          uuid (pk)
action      text NOT NULL
session_id  uuid NULL
user_id     text NULL
metadata    jsonb NULL
created_at  timestamptz DEFAULT now()
---------------------------------------------------------

Funciones expuestas:

- log_event(action, session_id=None, user_id=None, metadata=None)
- fetch_logs(limit=200)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .supabase_client import supabase

AUDIT_TABLE = "ca_audit_logs"


class AuditRepository:
    """
    Repositorio principal para logs de auditoría.
    """

    # ---------------------------------------------------------
    # Insertar un log
    # ---------------------------------------------------------
    def log_event(
        self,
        action: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        entry = {
            "action": action,
            "session_id": session_id,
            "user_id": user_id,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }

        try:
            supabase.table(AUDIT_TABLE).insert(entry).execute()
        except Exception as e:
            print("ERROR inserting into audit logs:", e)

    # ---------------------------------------------------------
    # Obtener logs para el panel
    # ---------------------------------------------------------
    def fetch_logs(self, limit: int = 200) -> List[Dict]:
        try:
            response = (
                supabase
                .table(AUDIT_TABLE)
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data or []
        except Exception as e:
            print("ERROR fetching audit logs:", e)
            return []


# Instancia global utilizada por todo el backend
audit_repository = AuditRepository()

# Alias directo para compatibilidad con views antiguas:
log_event = audit_repository.log_event
fetch_logs = audit_repository.fetch_logs
