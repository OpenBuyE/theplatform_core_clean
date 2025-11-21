"""
audit_repository.py
Sistema de auditoría basado en la tabla:
    ca_audit_logs

Esquema:
- id (uuid, PK)
- action (text)
- session_id (uuid, nullable)
- user_id (text, nullable)
- metadata (jsonb, nullable)
- created_at (timestamptz, default now())
"""

from datetime import datetime
from typing import Optional, Dict, Any, List

from .supabase_client import supabase


AUDIT_TABLE = "ca_audit_logs"


class AuditRepository:
    """
    Encapsula toda la lógica de auditoría.
    """

    # ---------------------------------------------------------
    # Registrar un evento en auditoría
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

        # Insertar en Supabase
        supabase.table(AUDIT_TABLE).insert(entry).execute()

    # ---------------------------------------------------------
    # Obtener logs (para el panel)
    # ---------------------------------------------------------
    def fetch_logs(
        self,
        limit: int = 200
    ) -> List[Dict[str, Any]]:

        response = (
            supabase
            .table(AUDIT_TABLE)
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        return response.data or []


# Instancia global (igual que el patrón que usamos en todo el backend)
audit_repository = AuditRepository()

# Función directa (para mantener compatibilidad con el backend actual)
def log_event(
    action: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    audit_repository.log_event(
        action=action,
        session_id=session_id,
        user_id=user_id,
        metadata=metadata,
    )
