# backend_core/services/session_engine.py

from __future__ import annotations

from typing import Optional
from datetime import datetime

from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event
from backend_core.services.session_repository import (
    get_session_by_id,
    finish_session,
    get_next_session_in_series,
)
from backend_core.services.module_repository import get_module_for_session
from backend_core.services.contract_engine import contract_engine


SESSIONS_TABLE = "ca_sessions"


class SessionEngine:
    """
    Gestiona expiraciones, rolling, validaciones.
    """

    # ============================================================
    # TRY ROLLING
    # ============================================================

    def try_rolling(self, finished_session_id: str):
        """
        Cuando una sesión se finaliza, activar la siguiente en su serie.
        """

        session = get_session_by_id(finished_session_id)
        if not session:
            return

        series_id = session["series_id"]
        seq = session["sequence_number"]

        next_session = get_next_session_in_series(series_id, seq)
        if not next_session:
            # No queda rolling pendiente
            log_event(
                "rolling_ended",
                session_id=finished_session_id,
                metadata={"series_id": series_id},
            )
            return

        # Activate next session
        now = datetime.utcnow().isoformat()

        (
            table(SESSIONS_TABLE)
            .update(
                {
                    "status": "active",
                    "activated_at": now,
                }
            )
            .eq("id", next_session["id"])
            .execute()
        )

        log_event(
            "rolling_session_started",
            session_id=next_session["id"],
            metadata={"previous_session": finished_session_id},
        )


# Global instance
session_engine = SessionEngine()
