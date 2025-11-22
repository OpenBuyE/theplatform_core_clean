# session_repository.py (VERSIÓN ESTABLE + ROLLING + COMPATIBLE)

from datetime import datetime, timedelta
from typing import List, Dict, Optional

from .supabase_client import supabase
from .audit_repository import log_event

SESSION_TABLE = "ca_sessions"
SERIES_TABLE = "ca_session_series"


class SessionRepository:

    # ---------------------------------------------------------
    # Obtener una sesión por ID
    # ---------------------------------------------------------
    def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        response = (
            supabase.table(SESSION_TABLE)
            .select("*")
            .eq("id", session_id)
            .single()
            .execute()
        )

        return response.data if response and response.data else None

    # ---------------------------------------------------------
    # Listar sesiones por estado
    # ---------------------------------------------------------
    def get_sessions(self, status: str = None, limit: int = 200) -> List[Dict]:
        query = supabase.table(SESSION_TABLE).select("*")

        if status:
            query = query.eq("status", status)

        response = query.limit(limit).execute()
        return response.data or []

    # ---------------------------------------------------------
    # Marcar una sesión como finished
    # ---------------------------------------------------------
    def mark_session_as_finished(self, session_id: str, finished_at: str):
        supabase.table(SESSION_TABLE).update({
            "status": "finished",
            "finished_at": finished_at
        }).eq("id", session_id).execute()

        log_event(
            action="session_finished",
            session_id=session_id,
            metadata={"finished_at": finished_at}
        )

    # ---------------------------------------------------------
    # Incrementar pax_registered
    # ---------------------------------------------------------
    def increment_pax_registered(self, session_id: str):
        session = self.get_session_by_id(session_id)
        if not session:
            return

        current = session.get("pax_registered", 0)
        new_value = current + 1

        supabase.table(SESSION_TABLE).update({
            "pax_registered": new_value
        }).eq("id", session_id).execute()

        log_event(
            action="pax_registered_incremented",
            session_id=session_id,
            metadata={"new_value": new_value}
        )

    # ---------------------------------------------------------
    # Crear nueva sesión parked
    # ---------------------------------------------------------
    def create_parked_session(
        self,
        product_id: str,
        organization_id: str,
        series_id: str,
        capacity: int,
    ) -> Optional[Dict]:

        now = datetime.utcnow().isoformat()

        new_session = {
            "product_id": product_id,
            "organization_id": organization_id,
            "series_id": series_id,
            "sequence_number": self._get_next_sequence_number(series_id),
            "status": "parked",
            "capacity": capacity,
            "pax_registered": 0,
            "created_at": now,
        }

        response = supabase.table(SESSION_TABLE).insert(new_session).execute()
        return response.data[0] if response.data else None

    # ---------------------------------------------------------
    # Obtener el siguiente sequence_number dentro de una serie
    # ---------------------------------------------------------
    def _get_next_sequence_number(self, series_id: str) -> int:
        response = (
            supabase.table(SESSION_TABLE)
            .select("sequence_number")
            .eq("series_id", series_id)
            .order("sequence_number")
            .execute()
        )

        rows = response.data or []
        if not rows:
            return 1

        seqs = [r["sequence_number"] for r in rows if r["sequence_number"]]
        return max(seqs) + 1 if seqs else 1

    # ---------------------------------------------------------
    # ACTIVAR sesión parked → active (5 días expiración)
    # ---------------------------------------------------------
    def activate_session(self, session_id: str) -> Optional[Dict]:

        expires_at = (datetime.utcnow() + timedelta(days=5)).isoformat()

        response = (
            supabase.table(SESSION_TABLE)
            .update({
                "status": "active",
                "activated_at": datetime.utcnow().isoformat(),
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
    # ROLLING — Obtener siguiente sesión parked en la serie
    # ---------------------------------------------------------
    def get_next_session_in_series(self, session: Dict) -> Optional[Dict]:
        """
        Busca dentro de la misma serie la siguiente sesión con status='parked'.
        """

        series_id = session.get("series_id")
        sequence = session.get("sequence_number")

        if not series_id:
            return None

        response = (
            supabase.table(SESSION_TABLE)
            .select("*")
            .eq("series_id", series_id)
            .eq("status", "parked")
            .order("sequence_number")
            .execute()
        )

        sessions = response.data or []
        return sessions[0] if sessions else None


# Instancia global
session_repository = SessionRepository()
