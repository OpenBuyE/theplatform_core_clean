# session_repository.py
# Gestiona sesiones CA (parked, active, finished)

from datetime import datetime, timedelta
from typing import List, Dict, Optional

from .supabase_client import supabase
from .audit_repository import log_event

SESSION_TABLE = "ca_sessions"


class SessionRepository:

    # ---------------------------------------------------------
    # Obtener sesiones
    # ---------------------------------------------------------
    def get_sessions(
        self,
        status: Optional[str] = None,
        limit: int = 200
    ) -> List[Dict]:

        query = supabase.table(SESSION_TABLE).select("*")

        if status:
            query = query.eq("status", status)

        response = query.limit(limit).execute()
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

        return response.data or None

    # ---------------------------------------------------------
    # Crear sesión parked
    # ---------------------------------------------------------
    def create_parked_session(
        self,
        product_id: str,
        organization_id: str,
        series_id: str,
        sequence_number: int,
        capacity: int,
    ) -> Dict:

        now = datetime.utcnow().isoformat()

        response = (
            supabase.table(SESSION_TABLE)
            .insert({
                "product_id": product_id,
                "organization_id": organization_id,
                "series_id": series_id,
                "sequence_number": sequence_number,
                "capacity": capacity,
                "status": "parked",
                "pax_registered": 0,
                "created_at": now,
            })
            .execute()
        )

        data = response.data[0]

        log_event(
            action="session_created",
            session_id=data["id"],
            metadata={"capacity": capacity}
        )

        return data

    # ---------------------------------------------------------
    # Activar sesión (PASO 4 actualizado)
    # ---------------------------------------------------------
    def activate_session(self, session_id: str) -> Optional[Dict]:

        now = datetime.utcnow()
        expires_at = (now + timedelta(days=5)).isoformat()

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

        if data:
            log_event(
                action="session_activated",
                session_id=session_id,
                metadata={"expires_at": expires_at},
            )

        return data

    # ---------------------------------------------------------
    # Marcar sesión como finished
    # ---------------------------------------------------------
    def mark_session_as_finished(self, session_id: str, finished_at: str) -> None:

        (
            supabase.table(SESSION_TABLE)
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

    # ---------------------------------------------------------
    # Incrementar pax_registered (bloqueo PASO 4)
    # ---------------------------------------------------------
    def increment_pax_registered(self, session_id: str) -> bool:

        session = self.get_session_by_id(session_id)
        if not session:
            return False

        current = session["pax_registered"]
        capacity = session["capacity"]

        # 👉 Nunca permitir superar aforo
        if current >= capacity:
            return False

        (
            supabase.table(SESSION_TABLE)
            .update({"pax_registered": current + 1})
            .eq("id", session_id)
            .execute()
        )

        return True


session_repository = SessionRepository()
