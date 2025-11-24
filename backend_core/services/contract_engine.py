# backend_core/services/contract_engine.py

from typing import Dict, Any, Optional

from backend_core.services.audit_repository import log_event
from backend_core.services.session_repository import get_session_by_id
from backend_core.services.module_repository import get_module_for_session
from backend_core.services.payment_state_machine import (
    init_payment_session,
    update_payment_state,
    get_payment_session,
)
from backend_core.services.wallet_orchestrator import wallet_orchestrator


class ContractEngine:
    """
    Motor contractual dependiente del módulo asignado.
    """

    def start_contract(self, session_id: str) -> None:
        session = get_session_by_id(session_id)
        module = get_module_for_session(session_id)

        log_event("contract_started", session_id=session_id, metadata=module)

        # Inicializar máquina de pagos solo si aplica
        if module and module["module_code"] == "DETERMINISTIC":
            init_payment_session(session_id)

    def on_deposit_ok(self, session_id: str) -> None:
        session = get_session_by_id(session_id)
        module = get_module_for_session(session_id)

        log_event("deposit_authorized", session_id=session_id)

        if module and module["module_code"] == "DETERMINISTIC":
            update_payment_state(session_id, "DEPOSITS_OK")

    def on_settlement_completed(self, session_id: str) -> None:
        session = get_session_by_id(session_id)
        module = get_module_for_session(session_id)

        log_event("settlement_completed", session_id=session_id)

        if module and module["module_code"] == "DETERMINISTIC":
            update_payment_state(session_id, "SETTLED")

    def on_force_majeure_refund(self, session_id: str) -> None:
        update_payment_state(session_id, "FORCE_MAJEURE")
        log_event("force_majeure_refund", session_id=session_id)


contract_engine = ContractEngine()

