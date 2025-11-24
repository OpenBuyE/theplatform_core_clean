# backend_core/services/contract_engine.py

from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime

from backend_core.services.audit_repository import log_event
from backend_core.services.session_repository import get_session_by_id
from backend_core.services.module_repository import get_session_module
from backend_core.services.payment_state_machine import (
    init_payment_session,
    get_payment_session,
    update_payment_state,
)


class ContractEngine:
    """
    Motor contractual OFF-CHAIN.
    Este archivo NO debe importar wallet_orchestrator arriba
    para evitar import circular.
    """

    # ============================================================
    # 1) Inicio de contrato
    # ============================================================

    def start_contract(self, session_id: str) -> Dict[str, Any]:

        session = get_session_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        module = get_session_module(session)

        if module["module_code"] != "A_DETERMINISTIC":
            return {"ok": False, "reason": "module does not support contracts"}

        # Obtener adjudicatario
        from backend_core.services.participant_repository import get_participants_for_session
        participants = get_participants_for_session(session_id)

        winner = next((p for p in participants if p["is_awarded"]), None)
        if not winner:
            raise RuntimeError("No awarded participant found")

        # Crear payment_session
        init_payment_session(session_id, winner["id"])

        log_event(
            "contract_started",
            session_id=session_id,
            metadata={"winner_id": winner["id"]},
        )

        return {"ok": True, "session_id": session_id, "winner": winner}

    # ============================================================
    # 2) Depósitos completados
    # ============================================================

    def on_participant_funded(self, session_id: str):
        """Llamado por wallet_orchestrator"""

        update_payment_state(session_id, "DEPOSITS_OK")

        log_event(
            "contract_funded",
            session_id=session_id,
        )

    # ============================================================
    # 3) Settlement completado
    # ============================================================

    def on_settlement_completed(self, session_id: str):
        """Llamado por wallet_orchestrator"""

        update_payment_state(session_id, "SETTLED")

        log_event(
            "contract_settlement_completed",
            session_id=session_id,
        )

    # ============================================================
    # 4) Reembolso por fuerza mayor
    # ============================================================

    def on_force_majeure_refund(self, session_id: str):
        """Llamado por wallet_orchestrator"""

        update_payment_state(session_id, "FORCE_MAJEURE")

        log_event(
            "contract_force_majeure",
            session_id=session_id,
        )

    # ============================================================
    # 5) Estado completo del contrato
    # ============================================================

    def get_contract_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = get_session_by_id(session_id)
        if not session:
            return None

        module = get_session_module(session)
        payment = get_payment_session(session_id)

        return {
            "session": session,
            "module": module,
            "payment": payment,
        }


# Instancia global
contract_engine = ContractEngine()
