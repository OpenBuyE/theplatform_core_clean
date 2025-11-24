# backend_core/services/adjudicator_engine.py

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import List, Dict, Any

from backend_core.services.audit_repository import log_event
from backend_core.services.session_repository import (
    get_session_by_id,
    get_participants_for_session,
    mark_awarded,
    finish_session,
    get_next_session_in_series,
)
from backend_core.services.module_repository import get_module_for_session
from backend_core.services.contract_engine import contract_engine
from backend_core.services.adjudicator_repository import (
    get_adjudication_seed,
)
from backend_core.services.session_engine import session_engine


class AdjudicatorEngine:

    # ============================================================
    # VALIDATE SESSION IS READY
    # ============================================================

    def _validate_ready_for_adjudication(self, session: Dict[str, Any]):
        if session["status"] != "active":
            raise ValueError("Session not active.")

        if session["pax_registered"] < session["capacity"]:
            raise ValueError("Session not full (capacity mismatch).")

    # ============================================================
    # COMPUTE DETERMINISTIC INDEX USING SHA256
    # ============================================================

    def _compute_awarded_index(self, session_id: str, participants: List[Dict[str, Any]]):
        seed_obj = get_adjudication_seed(session_id)
        public_seed = seed_obj["public_seed"] if seed_obj else ""

        base = (
            session_id +
            "".join([p["user_id"] for p in participants]) +
            public_seed
        )

        digest = hashlib.sha256(base.encode()).hexdigest()
        index = int(digest, 16) % len(participants)
        return index

    # ============================================================
    # MAIN ADJUDICATION FUNCTION
    # ============================================================

    def adjudicate_session(self, session_id: str):
        session = get_session_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        # Check module
        module = get_module_for_session(session_id)
        if not module:
            raise ValueError("Module not assigned to session")

        if module["module_type"] != "standard":
            raise ValueError("This module does not support adjudication")

        # validate state
        self._validate_ready_for_adjudication(session)

        # fetch participants
        participants = get_participants_for_session(session_id)
        if not participants:
            raise ValueError("No participants found")

        # compute index
        idx = self._compute_awarded_index(session_id, participants)
        awarded = participants[idx]

        # mark awarded
        mark_awarded(session_id, awarded["user_id"])

        log_event(
            "session_adjudicated",
            session_id=session_id,
            metadata={"awarded_user_id": awarded["user_id"]},
        )

        # finish session
        finish_session(session_id)

        # rolling
        next_session = get_next_session_in_series(session_id)
        if next_session:
            session_engine.activate_session(next_session["id"])

        # call contract engine
        contract_engine.start_contract_flow(session_id)


# ============================================================
# SINGLETON
# ============================================================

adjudicator_engine = AdjudicatorEngine()
