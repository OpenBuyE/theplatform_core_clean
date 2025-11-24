# backend_core/services/session_engine.py

from __future__ import annotations

from datetime import datetime
from typing import Optional

from backend_core.services.audit_repository import log_event
from backend_core.services.session_repository import (
    get_session_by_id,
    get_next_session_in_series,
    activate_session,
)


class SessionEngine:
    """
    Gestiona rolling y lógica de activación de la siguiente sesión en la serie.
    """

    def run_rolling_if_needed(self, finished_session_id: str) -> Optional[dict]:
        """
        Si hay una sesión siguiente en la serie, la activa.
        """

        finished = get_session_by_id(finished_session_id)
        if not finished:
            return None

        next_session = get_next_session_in_series(finished_session_id)
        if not next_session:
            # No hay rolling pendiente
            log_event(
                "rolling_not_available",
                session_id=finished_session_id,
                metadata={"series_id": finished.get("series_id")},
            )
            return None

        activate_session(next_session["id"])

        log_event(
            "rolling_session_started",
            session_id=next_session["id"],
            metadata={"previous_session_id": finished_session_id},
        )

        return next_session

    # Alias por compatibilidad con versiones anteriores
    def try_rolling(self, finished_session_id: str) -> Optional[dict]:
        return self.run_rolling_if_needed(finished_session_id)


# Instancia global
session_engine = SessionEngine()
