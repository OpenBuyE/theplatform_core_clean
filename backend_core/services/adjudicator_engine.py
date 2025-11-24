# backend_core/services/adjudicator_engine.py

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Dict, Optional

from backend_core.services.audit_repository import log_event
from backend_core.services.session_repository import (
    get_session_by_id,
    finish_session,
)
from backend_core.services.participant_repository import (
    get_participants_for_session,
    mark_awarded,
)
from backend_core.services.session_engine import session_engine
from backend_core.services.module_repository import get_session_module


class AdjudicatorEngine:

    def execute_adjudication(self, session_id: str) -> Optional[Dict]:

        session = get_session_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        module = get_session_module(session)

        if module["module_code"] != "A_DETERMINISTIC":
            raise ValueError("This module does not allow adjudication")

        participants = get_participants_for_session(session_id)

        if len(participants) < session["capacity"]:
            raise ValueError("Capacity not complete")

        # Deterministic seed
        seed_data = (
            session_id
            + session["series_id"]
            + str(session["sequence_number"])
            + "".join([p["id"] for p in participants])
        )
        seed_hash = hashlib.sha256(seed_data.encode()).hexdigest()

        winner_index = int(seed_hash, 16) % len(participants)
        winner = participants[winner_index]

        mark_awarded(session_id, winner["id"])

        finish_session(session_id)

        log_event(
            "session_awarded",
            session_id=session_id,
            metadata={"winner": winner, "seed_hash": seed_hash},
        )

        # Import diferido evita import circular
        from backend_core.services.contract_engine import contract_engine
        contract_engine.start_contract(session_id)

        # Rolling
        session_engine.process_rolling(session)

        return {"winner": winner, "seed_hash": seed_hash}


adjudicator_engine = AdjudicatorEngine()
