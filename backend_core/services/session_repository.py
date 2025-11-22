"""
session_repository.py (versión estable para ca_sessions)
"""

from datetime import datetime
from typing import List, Dict, Optional
from .supabase_client import supabase
from .audit_repository import log_event

SESSION_TABLE = "ca_sessions"


class SessionRepository:

    # ---------------------------------------------------------
    # Obtener sesiones por estado
    # ---------------------------------------------------------
    def get_sessions(
        self,
        status: Optional[str] = None,
        limit: int = 200
    ) -> List[Dict]:

        q = supabase.table(SESSION_TABLE).select("*")

        if status:
            q = q.eq("status", status)

        q = q.order("created_at", desc=True).limit(limit)
        res = q.execute()

        return res.data or []

    # ---------------------------------------------------------
    # Obtener sesión por ID
    # ---------------------------------------------------------
    def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        res = (
            supabase
            .table(SESSION_TABLE)
            .select("*")
            .eq("id", session_id)
            .single()
            .execute()
        )
        return res.data

    # ---------------------------------------------------------
    # Incrementar pax_registered
    # ---------------------------------------------------------
    def increment_pax_registered(self, session_id: str):
        (
            supabase
            .table(SESSION_TABLE)
            .update({"pax_registered": "pax_registered + 1"})
            .eq("id", session_id)
            .execute()
        )

    # ---------------------------------------------------------
    # Marcar sesión como FINISHED
    # ---------------------------------------------------------
    def mark_session_as_finished(self, session_id: str, finished_at: str):
        res = (
            supabase
            .table(SESSION_TABLE)
            .update({
                "status": "finished",
                "finished_at": finished_at
            })
            .eq("id", session_id)
            .execute()
        )

        log_event(
            action="session_marked_finished",
            session_id=session_id,
            metadata={"finished_at": finished_at}
        )

        return res.data[0] if res.data else None


session_repository = SessionRepository()
