"""
audit_repository.py
Gestión centralizada de logs para Compra Abierta,
almacenados en la tabla ca_audit_logs.

Estructura tabla:
- id (uuid)
- action (text)
- session_id (uuid, nullable)
- user_id (text, nullable)
- metadata (jsonb, nullable)
- created_at (timestamptz default now())
"""

from datetime import datetime
from typing import Optional, Dict, Any, List

from .supabase_client import supabase

AUDIT_TABLE = "ca_audit_logs"


# ---------------------------------------------------------
#  Insertar evento de auditoría
# ---------------------------------------------------------
def log_event(
    action: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Inserta un log en la tabla ca_audit_logs.
    Es tolerante a errores para no romper el flujo del backend.
    """

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
        # Si la auditoría falla, lo silenciamo  
        # para no provocar fallos visibles en el flujo.
        print(f"[AuditRepository] Error saving log: {e}")


# ---------------------------------------------------------
# Obtener logs recientes para el Panel
# ---------------------------------------------------------
def fetch_logs(limit: int = 200) -> List[Dict]:
    """
    Devuelve los últimos `limit` registros ordenados por fecha desc.
    """

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
        print(f"[AuditRepository] Error fetching logs: {e}")
        return []


# ---------------------------------------------------------
# Obtener logs filtrados por sesión
# ---------------------------------------------------------
def fetch_logs_by_session(session_id: str, limit: int = 200) -> List[Dict]:
    """
    Devuelve logs asociados a una sesión concreta.
    """

    try:
        response = (
            supabase
            .table(AUDIT_TABLE)
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    except Exception as e:
        print(f"[AuditRepository] Error fetching logs for session {session_id}: {e}")
        return []
