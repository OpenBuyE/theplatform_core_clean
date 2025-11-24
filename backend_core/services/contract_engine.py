# backend_core/services/contract_engine.py

from __future__ import annotations

from typing import Dict, Any
from datetime import datetime

from backend_core.services.audit_repository import log_event
from backend_core.services.session_repository import get_session_by_id
from backend_core.services.module_repository import get_module_for_session, mark_module_awarded
from backend_core.services.payment_state_machine import (
    init_payment_session,
    update_payment_state,
    get_payment_session,
)
from backend_core.services.wallet_orchestrator import wallet_orchestrator


class ContractEngine:

    def start_contract_flow(self, session_id: str):
        session = get_session_by_id(session_id)
        if not session:
            raise ValueError(f"No session found {session_id}")

        module = get_module_for_session(session_id)

        log_event(
            "contract_flow_started",
            session_id=session_id,
            metadata={"module_id": module["id"] if module else None},
        )

        init_payment_session(session_id)

    def confirm_delivery(self, session_id: str):
        update_payment_state(session_id, "DELIVERED")

        log_event("delivery_confirmed", session_id=session_id)

    def close_contract(self, session_id: str):
        now = datetime.utcnow().isoformat()

        module = get_module_for_session(session_id)
        if module:
            mark_module_awarded(module["id"])

        update_payment_state(session_id, "CLOSED")

        log_event("contract_closed", session_id=session_id, metadata={"closed_at": now})

    def handle_deposit_ok(self, payload: Dict[str, Any]):
        session_id = payload["session_id"]
        update_payment_state(session_id, "DEPOSITS_OK")
        log_event("deposit_ok_received", session_id=session_id)

    def handle_settlement(self, payload: Dict[str, Any]):
        session_id = payload["session_id"]
        update_payment_state(session_id, "SETTLED")
        log_event("settlement_completed", session_id=session_id)

    def handle_force_majeure(self, payload: Dict[str, Any]):
        session_id = payload["session_id"]
        update_payment_state(session_id, "FORCE_MAJEURE")
        log_event("force_majeure_refund", session_id=session_id)


contract_engine = ContractEngine()
