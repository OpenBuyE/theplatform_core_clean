"""
audit_repository.py
Sistema de auditoría centralizado para Compra Abierta.

Usa la tabla:
    ca_audit_logs

Esquema:

| id          | uuid (PK)
| action      | text (NOT NULL)
| session_id  | uuid (NULL)
| user_id     | text (NULL)
| metadata    | jsonb (NULL)
| created_at  | timestamptz (DEFAULT now())

"""

from datetime import datetime
from typing import Optional, Dict, Any, List

from .supabase_client import supabase

AUDIT_TABLE = "ca_audit_logs"


class AuditRepository:
    """
    Repositorio centralizado de auditoría.
    """

    # ---------------------------------------------------------
    # Registrar un evento de auditoría
    # ---------------------------------------------------------
    def log_event(
        self,
        action: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
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
    # Obtener eventos recientes (para el panel)
    # ---------------------------------------------------------
    def fetch_logs(self, limit: int = 200) -> List[Dict[str, Any]]:
        response = (
            supabase
            .table(AUDIT_TABLE)
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        return response.data or []


# Instancia global requerida por el panel
audit_repository = AuditRepository()
