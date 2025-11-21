"""
session_engine.py
Motor de sesiones para Compra Abierta.

Responsabilidades:
- Expirar sesiones activas que hayan superado el tiempo máximo
- Activar la siguiente sesión en la serie (rolling)
- Asegurar coherencia total con session_repository
"""

from datetime import datetime
from typing import Optional, Dict

from .session_repository import session_repository
from .audit_repository import log_event


class SessionEngine:

    # ---------------------------------------------------------
    #  Procesar expiraciones (sesiones activas que no completaron aforo)
    # ---------------------------------------------------------
    def process_expired_sessions(self) -> None:
        """
        Busca sesiones activas con expires_at < ahora.
        Las marca como finished SIN adjudicación.
        Activa la siguiente sesión en la serie (si existe).
        """

        now = datetime.utcnow().isoformat()
        expired = session_repository.get_active_sessions_expired(now)

        if not expired:
            return

        for session in expired:
            session_id = session["id"]

            # 1. Marcar finished sin adjudicación
            session_repository.mark_session_as_finished_without_award(
                session_id=session_id,
                finished_at=now
            )

            log_event(
                action="session_expired",
                session_id=session_id,
                metadata={"expires_at": session.get("expires_at")}
            )

            # 2. Activar siguiente sesión de la serie
            self.activate_next_session_in_series(session)

    # ---------------------------------------------------------
    #  Activar siguiente sesión en la serie
    # ---------------------------------------------------------
    def activate_next_session_in_series(self, session: Dict) -> Optional[Dict]:
        """
        Busca siguiente sesión parked:
        - mismo series_id
        - sequence_number > actual
        - status = parked
        Activa la de menor sequence_number.

        Devuelve la sesión activada o None.
        """

        next_session = session_repository.get_next_session_in_series(session)

        if not next_session:
            log_event(
                action="rolling_no_next_session",
                session_id=session["id"],
                metadata={
                    "series_id": session.get("series_id"),
                    "sequence_number": session.get("sequence_number")
                }
            )
            return None

        activated = session_repository.activate_session(next_session["id"])

        log_event(
            action="rolling_session_activated",
            session_id=session["id"],
            metadata={
                "activated_session_id": next_session["id"],
                "next_sequence": next_session["sequence_number"]
            }
        )

        return activated


# Instancia global usada en el backend
session_engine = SessionEngine()
