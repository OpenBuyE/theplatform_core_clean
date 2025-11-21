"""
session_repository.py
Repositorio de sesiones para Compra Abierta.

Responsabilidades reales:
- Obtener sesiones por estado, serie, organización
- Obtener una sesión por id
- Activar sesión (parked → active)
- Marcar sesiones como finished (con adjudicación)
- Marcar como finished sin adjudicación (expirada)
- Incrementar pax_registered
- Obtener sesiones expiradas
- Obtener siguiente sesión de la serie (rolling)
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional

from .supabase_client import supabase
from .audit_repository import log_event


SESSION_TABLE = "sessions"


class SessionRepository:

    # ---------------------------------------------------------
    #  Obtener sesión por ID
    # ---------------------------------------------------------
    def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        response = (
            supabase.table(SESSION_TABLE)
            .select("*")
            .eq("id", session_id)
            .maybe_single()
            .execute()
        )
        return response.data

    # ---------------------------------------------------------
    #  Obtener lista de sesiones (filtros simples)
    # ---------------------------------------------------------
    def get_sessions(
        self,
        status: Optional[str] = None,
        organization_id: Optional[str] = None,
        series_id: Optional[str] = None,
        limit: int = 200
    ) -> List[Dict]:
        query = supabase.table(SESSION_TABLE).select("*")

        if status:
            query = query.eq("status", status)
        if organization_id:
            query = query.eq("organization_id", organization_id)
        if series_id:
            query = query.eq("series_id", series_id)

        response = query.order("created_at", desc=True).limit(limit).execute()
        return response.data or []

    # ---------------------------------------------------------
    #  Obtener sesiones parked
    # ---------------------------------------------------------
    def get_parked_sessions(
        self,
        organization_id: Optional[str] = None,
        series_id: Optional[str] = None,
        limit=200
    ) -> List[Dict]:
        return self.get_sessions(
            status="parked",
            organization_id=organization_id,
            series_id=series_id,
            limit=limit
        )

    # ---------------------------------------------------------
    #  Activar sesión parked -> active
    # ---------------------------------------------------------
    def activate_session(
        self,
        session_id: str,
        expires_at: Optional[str] = None
    ) -> Optional[Dict]:

        now = datetime.utcnow()

        if expires_at is None:
            expires_dt = now + timedelta(days=5)
            expires_at = expires_dt.isoformat()

        response = (
            supabase.table(SESSION_TABLE)
            .update({
                "status": "active",
                "activated_at": now.isoformat(),
                "expires_at": expires_at
            })
            .eq("id", session_id)
            .execute()
        )

        data = response.data[0] if response.data else None

        log_event(
            action="session_activated",
            session_id=session_id,
            metadata={"expires_at": expires_at}
        )

        return data

    # ---------------------------------------------------------
    #  Marcar sesión finished (tras adjudicación)
    # ---------------------------------------------------------
    def mark_session_as_finished(self, session_id: str, finished_at: str):
        supabase.table(SESSION_TABLE).update({
            "status": "finished",
            "finished_at": finished_at
        }).eq("id", session_id).execute()

        log_event(
            action="session_marked_finished",
            session_id=session_id,
            metadata={"finished_at": finished_at}
        )

    # ---------------------------------------------------------
    #  Marcar como finished sin adjudicación (expirada)
    # ---------------------------------------------------------
    def mark_session_as_finished_without_award(self, session_id: str, finished_at: str):
        supabase.table(SESSION_TABLE).update({
            "status": "finished",
            "finished_at": finished_at
        }).eq("id", session_id).execute()

        log_event(
            action="session_expired",
            session_id=session_id,
            metadata={"finished_at": finished_at}
        )

    # ---------------------------------------------------------
    #  Incrementar pax_registered
    # ---------------------------------------------------------
    def increment_pax_registered(self, session_id: str):
        session = self.get_session_by_id(session_id)
        if not session:
            log_event(
                action="increment_pax_failed_session_not_found",
                session_id=session_id
            )
            return

        new_value = session.get("pax_registered", 0) + 1

        supabase.table(SESSION_TABLE).update({
            "pax_registered": new_value
        }).eq("id", session_id).execute()

        log_event(
            action="pax_incremented",
            session_id=session_id,
            metadata={"new_value": new_value}
        )

    # ---------------------------------------------------------
    #  Sesiones activas caducadas (motor expiración)
    # ---------------------------------------------------------
    def get_active_sessions_expired(self, now_iso: str) -> List[Dict]:
        response = (
            supabase.table(SESSION_TABLE)
            .select("*")
            .eq("status", "active")
            .lt("expires_at", now_iso)
            .execute()
        )
        return response.data or []

    # ---------------------------------------------------------
    #  Siguiente sesión de la serie (rolling)
    # ---------------------------------------------------------
    def get_next_session_in_series(self, session: Dict) -> Optional[Dict]:
        series_id = session.get("series_id")
        seq = session.get("sequence_number")

        if not series_id or seq is None:
            return None

        response = (
            supabase.table(SESSION_TABLE)
            .select("*")
            .eq("series_id", series_id)
            .eq("status", "parked")
            .gt("sequence_number", seq)
            .order("sequence_number", asc=True)
            .limit(1)
            .execute()
        )

        return response.data[0] if response.data else None


# ---------------------------------------------------------
# Instancia global del repositorio
# ---------------------------------------------------------
session_repository = SessionRepository()
