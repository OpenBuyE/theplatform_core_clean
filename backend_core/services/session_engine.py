# backend_core/services/session_engine.py

from __future__ import annotations

from typing import Dict, Any
from datetime import datetime, timedelta

from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event
from backend_core.services.session_repository import (
    get_session_by_id,
    get_next_session_in_series,
    activate_session,
    finish_session,
)
from backend_core.services.module_repository import get_module_for_session
from backend_core.services.contract_engine import contract_engine


class SessionEngine:

    def check_expired(self, session_id: str):
        session = get_session_by_id(session_id)
        if not session:
            return

        if session["status"] != "active":
            return

        expires_at = session.get("expires_at")
        if not expires_at:
            return

        now = datetime.utcnow()
        exp = datetime.fromisoformat(expires_at.replace("Z", ""))

        if now > exp:
            finish_session(session_id)
            log_event("session_expired", session_id=session_id)

    def activate_session(self, session_id: str):
        """Wrapper para mantener compatibilidad."""
        activate_session(session_id)

    def run_rolling_if_needed(self, session_id: str):
        next_sess = get_next_session_in_series(session_id)
        if next_sess:
            self.activate_session(next_sess["id"])
            log_event(
                "rolling_session_started",
                session_id=next_sess["id"],
                metadata={"previous_session": session_id},
            )


session_engine = SessionEngine()
