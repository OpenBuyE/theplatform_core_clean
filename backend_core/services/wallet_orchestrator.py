# backend_core/services/wallet_orchestrator.py
from __future__ import annotations

from datetime import datetime

from backend_core.models.payment_state import (
    PaymentEvent,
)
from backend_core.services.payment_session_repository import (
    get_payment_session_by_session_id,
    save_payment_session,
    to_state_snapshot,
)
from backend_core.services.payment_state_machine import PaymentStateMachine
from backend_core.services.wallet_events import (
    DepositOkEvent,
    SettlementCompletedEvent,
    ForceMajeureRefundEvent,
)
from backend_core.services.audit_repository import AuditRepository
from backend_core.services import contract_engine


class WalletOrchestrator:
    def __init__(self, audit_repo: AuditRepository):
        self.audit_repo = audit_repo

    # ------------------------------
    # Helpers internos
    # ------------------------------

    def _load(self, session_id: str):
        ps = get_payment_session_by_session_id(session_id)
        if ps is None:
            raise ValueError(f"No payment_session found for session {session_id}")
        return ps

    # ------------------------------
    # Handlers
    # ------------------------------

    def handle_deposit_ok(self, event: DepositOkEvent) -> None:
        ps = self._load(event.session_id)

        # actualizamos el depósito acumulado
        ps.total_deposited_amount = (ps.total_deposited_amount or 0.0) + event.amount

        snapshot = to_state_snapshot(ps)
        new_snapshot = PaymentStateMachine.transition(
            snapshot,
            PaymentEvent.PARTICIPANT_DEPOSIT_AUTHORIZED,
        )

        # Guardamos cambios en la entidad persistente
        ps.status = new_snapshot.status
        ps.force_majeure = new_snapshot.force_majeure
        ps.updated_at = datetime.utcnow()
        save_payment_session(ps)

        # Auditoría
        self.audit_repo.log(
            action="DEPOSIT_OK",
            session_id=event.session_id,
            user_id=event.user_id,
            metadata={
                "amount": event.amount,
                "ftx_op": event.fintech_operation_id,
                "raw": event.raw_payload,
            },
        )

        # Informar al contract_engine
        contract_engine.on_participant_funded(
            session_id=event.session_id,
            user_id=event.user_id,
            amount=event.amount,
            fintech_operation_id=event.fintech_operation_id,
        )

    # ----------------------------------------

    def mark_all_deposits_ok(self, session_id: str) -> None:
        ps = self._load(session_id)
        snapshot = to_state_snapshot(ps)

        new_snapshot = PaymentStateMachine.transition(
            snapshot,
            PaymentEvent.ALL_DEPOSITS_OK,
        )

        ps.status = new_snapshot.status
        ps.updated_at = datetime.utcnow()
        save_payment_session(ps)

        self.audit_repo.log(
            action="ALL_DEPOSITS_OK",
            session_id=session_id,
            user_id=None,
        )

    # ----------------------------------------

    def handle_settlement_completed(self, event: SettlementCompletedEvent) -> None:
        ps = self._load(event.session_id)

        ps.total_settled_amount = (ps.total_settled_amount or 0.0) + event.amount

        snapshot = to_state_snapshot(ps)
        new_snapshot = PaymentStateMachine.transition(
            snapshot,
            PaymentEvent.SETTLEMENT_CONFIRMED,
        )

        ps.status = new_snapshot.status
        ps.updated_at = datetime.utcnow()
        save_payment_session(ps)

        self.audit_repo.log(
            action="SETTLEMENT_COMPLETED",
            session_id=event.session_id,
            user_id=None,
            metadata={
                "amount": event.amount,
                "provider_id": event.provider_id,
                "ftx_op": event.fintech_operation_id,
                "raw": event.raw_payload,
            },
        )

        contract_engine.on_settlement_completed(
            session_id=event.session_id,
            provider_id=event.provider_id,
            amount=event.amount,
            fintech_operation_id=event.fintech_operation_id,
        )

    # ----------------------------------------

    def handle_force_majeure_refund(self, event: ForceMajeureRefundEvent) -> None:
        ps = self._load(event.session_id)

        snapshot = to_state_snapshot(ps)
        new_snapshot = PaymentStateMachine.transition(
            snapshot,
            PaymentEvent.FORCE_MAJEURE_TRIGGERED,
        )

        ps.status = new_snapshot.status
        ps.force_majeure = True
        ps.updated_at = datetime.utcnow()
        save_payment_session(ps)

        self.audit_repo.log(
            action="FORCE_MAJEURE_REFUND",
            session_id=event.session_id,
            user_id=event.adjudicatario_user_id,
            metadata={
                "amount_refunded": event.amount_refunded,
                "ftx_op": event.fintech_operation_id,
                "raw": event.raw_payload,
            },
        )

        contract_engine.on_force_majeure_refund(
            session_id=event.session_id,
            adjudicatario_user_id=event.adjudicatario_user_id,
            amount_refunded=event.amount_refunded,
            fintech_operation_id=event.fintech_operation_id,
        )
