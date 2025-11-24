# backend_core/services/adjudicator_engine.py

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Dict, Any, List

from backend_core.services.audit_repository import log_event
from backend_core.services.session_repository import (
    get_session_by_id,
    get_participants_for_session,
    mark_awarded,
    finish_session,
)
from backend_core.services.session_engine import session_engine
from backend_core.services.module_repository import (
    get_module_for_session,
    mark_module_awarded,
)
from backend_core.services.contract_engine import contract_engine
from backend_core.services.adjudicator_repository import get_seed_for_session


class AdjudicatorEngine:

    # ============================================================
    # RUN ADJUDICATION
    # ============================================================

    def run_adjudication(self, session_id: str) -> Dict[str, Any]:
        session = get_session_by_id(session_id)
        if not session:
            raise ValueError("Session not found.")

        participants = get_participants_for_session(session_id)
        if not participants:
            raise ValueError("No participants in session.")

        # Verify capacity reached
        if session["pax_registered"] < session["capacity"]:
            raise ValueError("Session aforo not completed.")

        # Get module
        module = get_module_for_session(session_id)
        if not module:
            raise ValueError("Module not found for session.")

        # Get deterministic public seed
        seed = get_seed_for_session(session_id)

        # Build deterministic payload
        concatenated = (
            session_id +
            session["series_id"] +
            str(session["sequence_number"]) +
            "".join([p["id"] for p in participants]) +
            (seed["public_seed"] if seed else "DEFAULT")
        )

        digest = hashlib.sha256(concatenated.encode()).hexdigest()
        winner_index = int(digest, 16) % len(participants)
        awarded = participants[winner_index]

        # Mark awarded participant
        mark_awarded(awarded["id"])

        # Mark module as awarded
        mark_module_awarded(module["id"])

        # Finish session
        finish_session(session_id)

        log_event(
            "session_adjudicated",
            session_id=session_id,
            metadata={
                "awarded_participant": awarded["id"],
                "hash": digest,
                "winner_index": winner_index,
            },
        )

        # Contract engine → start contract logic
        contract_engine.on_session_awarded(session_id, awarded["id"])

        # Rolling
        session_engine.try_rolling(session_id)

        return {
            "session_id": session_id,
            "awarded_participant": awarded,
        }


# Global instance
adjudicator_engine = AdjudicatorEngine()
