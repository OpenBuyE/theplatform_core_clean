"""
session_engine.py
Funciones de alto nivel sobre sesiones:
- Activar siguiente sesión (rolling)
"""

from datetime import datetime

from .session_repository import session_repository
from .audit_repository import log_event


class SessionEngine:

    # ---------------------------------------------------------
    # Activar siguiente sesión parked de la serie
    # ---------------------------------------------------------
    def activate_next_session_in_series(self, session: dict):

        next_session = session_repository.get_next_session_in_series(session)

        if not next_session:
            log_event(
                action="no_next_session_in_series",
                session_id=session["id"],
                metadata={"series_id": session["series_id"]},
            )
            return None

        activated = session_repository.activate_session(next_session["id"])

        if activated:
            log_event(
                action="next_session_activated",
                session_id=session["id"],
                metadata={"activated_id": activated["id"]},
            )

        return activated


session_engine = SessionEngine()
