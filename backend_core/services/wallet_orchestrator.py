# backend_core/services/wallet_orchestrator.py

from __future__ import annotations

from typing import Dict, Any

from backend_core.services.audit_repository import log_event
from backend_core.services.payment_state_machine import (
    get_payment_session,
    update_payment_state,
    mark_settlement,
    mark_force_majeure_refund,
)
from backend_core.services.contract_engine import contract_engine


class WalletOrchestrator:
    """
    Orquestador de eventos provenientes de MangoPay (webhooks simulados).
    Este componente decide cómo modificar el estado de payment_session
    y cuándo avanzar el flujo contractual.
    """

    # ============================================================
    # 1) DEPÓSITO OK (todos los compradores completan pago)
    # ============================================================

    def handle_deposit_ok(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evento que indica que MangoPay confirma los depósitos
        de todos los participantes.
        """

        # Actualizamos estado
        updated = update_payment_state(session_id, "DEPOSITS_OK")

        log_event(
            "wallet_deposit_ok",
            session_id=session_id,
            metadata={"payload": payload, "new_status": "DEPOSITS_OK"},
        )

        # Avisar al motor contractual
        contract_engine.on_participant_funded(session_id)

        return {"ok": True, "payment": updated}

    # ============================================================
    # 2) EJECUCIÓN DE LIQUIDACIÓN (pago al proveedor)
    # ============================================================

    def handle_settlement_executed(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evento que indica que MangoPay ha ejecutado la transferencia
        al proveedor.
        """

        updated = mark_settlement(session_id)

        log_event(
            "wallet_settlement_executed",
            session_id=session_id,
            metadata={"payload": payload, "new_status": "SETTLED"},
        )

        contract_engine.on_settlement_completed(session_id)

        return {"ok": True, "payment": updated}

    # ============================================================
    # 3) REEMBOLSO POR FUERZA MAYOR
    # ============================================================

    def handle_force_majeure_refund(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evento emitido cuando MangoPay reembolsa solo el precio del producto
        en caso de fuerza mayor.
        """

        updated = mark_force_majeure_refund(session_id)

        log_event(
            "wallet_force_majeure_refund",
            session_id=session_id,
            metadata={"payload": payload, "new_status": "FORCE_MAJEURE"},
        )

        contract_engine.on_force_majeure_refund(session_id)

        return {"ok": True, "payment": updated}


# Instancia global
wallet_orchestrator = WalletOrchestrator()
