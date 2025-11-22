"""
session_repository.py
Repositorio de sesiones para Compra Abierta (ca_sessions)

Incluye:
- Crear sesión
- Activar sesión
- Marcar finished
- Incrementar pax_registered
- Obtener siguiente sesión en la serie (rolling)
"""

from typing import List, Dict, Optional
from datetime import datetime

from .supabase_client import supabase
from .audit_repository import log_event

SESSION_TABLE = "ca_sessions"
SERIES_TABLE = "ca_session_series"


class SessionRepository:

    # ---------------------------------------------------------
    # Crear sesión parked vinculada a una serie
    # ---------------------------------------------------------
    def create_session(
        self,
        product_id: str,
        organization_id: str,
        series_id: str,
        sequence_number: int,
        capacity: int,
    ) -> Optional[Dict]:

        now = datetime.utcnow().isoformat()

        payload = {
            "product_id": product_id,
            "organization_id": organization_id,
            "series_id": series_id,
            "sequence_number": sequence_number,
            "status": "parked",
            "capacity": capacity,
            "pax_registered": 0,
            "created_at": now,
        }

        response = supabase.table(SESSION_TABLE).insert(payload).execute()

        if not response.data:
            return None

        return response.data[0]

    # ---------------------------------------------------------
    # Obtener sesiones (filtros opcionales)
    # ---------------------------------------------------------
    def get_sessions(
        self,
        status: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict]:

        query = supabase.table(SESSION_TABLE).select("*")

        if status:
            query = query.eq("status", status)

        query = query.order("created_at", desc=False).limit(limit)
        response = query.execute()

        return response.data or []

    # ---------------------------------------------------------
    # Obtener sesión por ID
    # ---------------------------------------------------------
    def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        response = (
            supabase.table(SESSION_TABLE)
            .select("*")
            .eq("id", session_id)
            .single()
            .execute()
        )

        return response.data if response else None

    # ---------------------------------------------------------
    # Activar sesión
    # ---------------------------------------------------------
    def activate_session(self, session_id: str) -> Optional[Dict]:
        now = datetime.utcnow().isoformat()

        expires_at = (
            datetime.utcnow()
            .replace(microsecond=0)
            .isoformat()
        )

        response = (
            supabase.table(SESSION_TABLE)
            .update({
                "status": "active",
                "activated_at": now,
                "expires_at": expires_at,
            })
            .eq("id", session_id)
            .execute()
        )

        if not response.data:
            return None

        data = response.data[0]

        log_event(
            action="session_activated",
            session_id=session_id,
            metadata={"expires_at": expires_at},
        )

        return data

    # ---------------------------------------------------------
    # Incrementar pax_registered
    # ---------------------------------------------------------
    def increment_pax_registered(self, session_id: str) -> None:
        session = self.get_session_by_id(session_id)
        if not session:
            return None

        new_pax = session.get("pax_registered", 0) + 1

        supabase.table(SESSION_TABLE).update({
            "pax_registered": new_pax
        }).eq("id", session_id).execute()

    # ---------------------------------------------------------
    # Marcar sesión como finalizada
    # ---------------------------------------------------------
    def mark_session_as_finished(self, session_id: str, finished_at: str) -> None:
        supabase.table(SESSION_TABLE).update({
            "status": "finished",
            "finished_at": finished_at,
        }).eq("id", session_id).execute()

        log_event(
            action="session_finished",
            session_id=session_id,
            metadata={"finished_at": finished_at},
        )

    # ---------------------------------------------------------
    # Obtener la siguiente sesión de la serie
    # ---------------------------------------------------------
    def get_next_session_in_series(self, session: Dict) -> Optional[Dict]:

        series_id = session["series_id"]
        seq = session["sequence_number"]

        response = (
            supabase.table(SESSION_TABLE)
            .select("*")
            .eq("series_id", series_id)
            .eq("status", "parked")
            .gt("sequence_number", seq)
            .order("sequence_number", desc=False)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return response.data[0]


# Singleton global
session_repository = SessionRepository()
