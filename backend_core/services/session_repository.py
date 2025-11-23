"""
session_repository.py
Repositorio de sesiones para Compra Abierta (tabla ca_sessions).

Responsabilidades:
- Obtener sesiones por estado, serie, organización
- Obtener una sesión por id
- Marcar sesiones como finished (con o sin adjudicación)
- Incrementar pax_registered
- Listar sesiones activas y expiradas
- Activar siguiente sesión (parked -> active) para rolling
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional

from .supabase_client import supabase
from .audit_repository import log_event

SESSION_TABLE = "ca_sessions"


class SessionRepository:
    # ---------------------------------------------------------
    #  Obtener una sesión por ID
    # ---------------------------------------------------------
    def get_session_by_id(self, session_id: str) -> Optional[Dict]:
        response = (
            supabase
            .table(SESSION_TABLE)
            .select("*")
            .eq("id", session_id)
            .maybe_single()
            .execute()
        )
        return response.data

    # ---------------------------------------------------------
    #  Obtener lista de sesiones (para panel, filtros básicos)
    # ---------------------------------------------------------
    def get_sessions(
        self,
        status: Optional[str] = None,
        organization_id: Optional[str] = None,
        series_id: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict]:
        query = supabase.table(SESSION_TABLE).select("*")

        if status:
            query = query.eq("status", status)
        if organization_id:
            query = query.eq("organization_id", organization_id)
        if series_id:
            query = query.eq("series_id", series_id)

        # supabase-py: order(col, desc=bool)
        query = query.order("created_at", desc=True).limit(limit)

        response = query.execute()
        return response.data or []

    # ---------------------------------------------------------
    #  Obtener sesiones parked
    # ---------------------------------------------------------
    def get_parked_sessions(
        self,
        organization_id: Optional[str] = None,
        series_id: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict]:
        return self.get_sessions(
            status="parked",
            organization_id=organization_id,
            series_id=series_id,
            limit=limit,
        )

    # ---------------------------------------------------------
    #  Activar una sesión (parked -> active)
    # ---------------------------------------------------------
    def activate_session(
        self,
        session_id: str,
        expires_at: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Activa una sesión parked.
        Si no se pasa expires_at, se asume ventana de 5 días desde ahora.
        """
        now = datetime.utcnow()
        if expires_at is None:
            expires_dt = now + timedelta(days=5)
            expires_at = expires_dt.isoformat()

        response = (
            supabase
            .table(SESSION_TABLE)
            .update({
                "status": "active",
                "activated_at": now.isoformat(),
                "expires_at": expires_at,
            })
            .eq("id", session_id)
            .execute()
        )

        data = response.data[0] if response.data else None

        log_event(
            action="session_activated",
            session_id=session_id,
            metadata={"expires_at": expires_at},
        )

        return data

    # ---------------------------------------------------------
    #  Marcar sesión como finished (con adjudicación)
    # ---------------------------------------------------------
    def mark_session_as_finished(self, session_id: str, finished_at: str) -> None:
        (
            supabase
            .table(SESSION_TABLE)
            .update({
                "status": "finished",
                "finished_at": finished_at,
            })
            .eq("id", session_id)
            .execute()
        )

        log_event(
            action="session_marked_finished",
            session_id=session_id,
            metadata={"finished_at": finished_at},
        )

    # ---------------------------------------------------------
    #  Marcar sesión como finished SIN adjudicación (expirada)
    # ---------------------------------------------------------
    def mark_session_as_finished_without_award(
        self,
        session_id: str,
        finished_at: str,
    ) -> None:
        (
            supabase
            .table(SESSION_TABLE)
            .update({
                "status": "finished",
                "finished_at": finished_at,
            })
            .eq("id", session_id)
            .execute()
        )

        log_event(
            action="session_marked_finished_without_award",
            session_id=session_id,
            metadata={"finished_at": finished_at},
        )

    # ---------------------------------------------------------
    #  Incrementar pax_registered (cuando entra un participante)
    # ---------------------------------------------------------
    def increment_pax_registered(self, session_id: str) -> Optional[Dict]:
        """
        Incrementa pax_registered de la sesión en 1.

        Nota: este método hace:
        - lee la sesión
        - suma 1
        - guarda el valor

        Para el estado actual del proyecto es suficiente.
        """
        session = self.get_session_by_id(session_id)
        if not session:
            log_event(
                action="increment_pax_error_session_not_found",
                session_id=session_id,
            )
            return None

        current = session.get("pax_registered", 0)
        new_value = current + 1

        response = (
            supabase
            .table(SESSION_TABLE)
            .update({"pax_registered": new_value})
            .eq("id", session_id)
            .execute()
        )

        updated = response.data[0] if response.data else None

        log_event(
            action="pax_registered_incremented",
            session_id=session_id,
            metadata={
                "previous": current,
                "new": new_value,
            },
        )

        return updated

    # ---------------------------------------------------------
    #  Obtener sesiones activas ya expiradas (para motor de expiración)
    # ---------------------------------------------------------
    def get_active_sessions_expired(self, now_iso: str) -> List[Dict]:
        """
        Devuelve sesiones con:
        - status = 'active'
        - expires_at < now_iso
        """
        response = (
            supabase
            .table(SESSION_TABLE)
            .select("*")
            .eq("status", "active")
            .lt("expires_at", now_iso)
            .execute()
        )

        return response.data or []

    # ---------------------------------------------------------
    #  Buscar siguiente sesión de la serie (para rolling)
    # ---------------------------------------------------------
    def get_next_session_in_series(self, session: Dict) -> Optional[Dict]:
        """
        Dada una sesión, busca la siguiente de la misma serie
        con sequence_number mayor y status = 'parked',
        escogiendo la de menor sequence_number posible.
        """
        series_id = session.get("series_id")
        sequence_number = session.get("sequence_number")

        if not series_id or sequence_number is None:
            return None

        response = (
            supabase
            .table(SESSION_TABLE)
            .select("*")
            .eq("series_id", series_id)
            .eq("status", "parked")
            .gt("sequence_number", sequence_number)
            .order("sequence_number", desc=False)
            .limit(1)
            .execute()
        )

        data = response.data or []
        if not data:
            return None

        return data[0]


# Instancia global exportable
session_repository = SessionRepository()
