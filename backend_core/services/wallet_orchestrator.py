# backend_core/services/wallet_orchestrator.py

from __future__ import annotations

from typing import Dict, Any

from backend_core.services.audit_repository import log_event
from backend_core.services.payment_state_machine import (
    update_payment_state,
)


class WalletOrchestrator:
    """
    Orquesta eventos de MangoPay.
    Importamos contract_engine SOLO dentro de funciones para evitar import circular.
    """

    def handle_deposit_ok(self, session_id: str, payload: Dict[str, Any]):
        from backend_core.services.contract_engine import contract_engine

        update_payment_state(session_id, "DEPOSITS_OK")

        log_event("wallet_deposit_ok", session_id=session_id, metadata=payload)

        contract_engine.on_participant_funded(session_id)

        return {"ok": True}

    def handle_settlement_executed(self, session_id: str, payload: Dict[str, Any]):
        from backend_core.services.contract_engine import contract_engine

        update_payment_state(session_id, "SETTLED")

        log_event("wallet_settlement_executed", session_id=session_id, metadata=payload)

        contract_engine.on_settlement_completed(session_id)

        return {"ok": True}

    def handle_force_majeure_refund(self, session_id: str, payload: Dict[str, Any]):
        from backend_core.services.contract_engine import contract_engine

        update_payment_state(session_id, "FORCE_MAJEURE")

        log_event("wallet_force_majeure_refund", session_id=session_id, metadata=payload)

        contract_engine.on_force_majeure_refund(session_id)

        return {"ok": True}


wallet_orchestrator = WalletOrchestrator()
