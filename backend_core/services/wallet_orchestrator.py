# backend_core/services/wallet_orchestrator.py
from __future__ import annotations

from datetime import datetime

from backend_core.models.payment_state import (
    PaymentEvent,
    PaymentStateSnapshot,
)
from backend_core.services import supabase_client
from backend_core.services.audit_repository import AuditRepository
from backend_core.services import contract_engine
from backend_core.services.payment_state_machine import PaymentStateMachine
from backend_core.services.wallet_events import (
    DepositOkEvent,
    SettlementCompletedEvent,
    ForceMajeureRefundEvent,
)


class WalletOrchestrator:
    """
    Orquestador central para eventos de wallet / fintech.
    NO ejecuta lógica contractual directamente: delega en contract_engine.
    """

    def __init__(self, audit_repo: AuditRepository):
        self.audit_repo = audit_repo

    # ---------- Helpers internos ----------

    def _load_payment_state(self, session_id: str) -> PaymentStateSnapshot:
        """
        Carga la fila de payment_session desde Supabase y la proyecta
        a PaymentStateSnapshot.
        ADAPTA al nombre real de tu tabla, por ejemplo: ca_payment_sessions
        """
        resp = (
            supabase_client.table("ca_payment_sessions")
            .select("*")
            .eq("session_id", session_id)
            .single()
            .execute()
        )
        row = resp.data

        return PaymentStateSnapshot(
            payment_session_id=row["id"],
            session_id=row["session_id"],
            status=row["status"],
            total_expected_amount=row.get("total_expected_amount"),
            total_deposited_amount=row.get("total_deposited_amount"),
            total_settled_amount=row.get("total_settled_amount"),
            force_majeure=row.get("force_majeure", False),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            metadata=row.get("metadata") or {},
        )

    def _save_payment_state(self, snapshot: PaymentStateSnapshot) -> None:
        """
        Persiste el snapshot en Supabase.
        """
        supabase_client.table("ca_payment_sessions").update(
            {
                "status": snapshot.status.value,
                "total_expected_amount": snapshot.total_expected_amount,
                "total_deposited_amount": snapshot.total_deposited_amount,
                "total_settled_amount": snapshot.total_settled_amount,
                "force_majeure": snapshot.force_majeure,
                "updated_at": snapshot.updated_at.isoformat(),
                "metadata": snapshot.metadata,
            }
        ).eq("id", snapshot.payment_session_id).execute()

    # ---------- Handlers públicos ----------

    def handle_deposit_ok(self, event: DepositOkEvent) -> None:
        """
        1. Actualiza PaymentState (podría seguir en WAITING_DEPOSITS).
        2. Registra en auditoría.
        3. Informa al contract_engine (on_participant_funded).
        """
        snapshot = self._load_payment_state(event.session_id)

        # Aquí puedes sumar a total_deposited_amount, etc. antes o después:
        snapshot.total_deposited_amount = (snapshot.total_deposited_amount or 0.0) + event.amount

        # Disparamos evento de "deposit authorized" (no cambia de estado global todavía):
        new_snapshot = PaymentStateMachine.transition(
            snapshot,
            PaymentEvent.PARTICIPANT_DEPOSIT_AUTHORIZED,
        )

        self._save_payment_state(new_snapshot)

        # Auditoría
        self.audit_repo.log(
            action="DEPOSIT_OK",
            session_id=event.session_id,
            user_id=event.user_id,
            metadata={
                "fintech_operation_id": event.fintech_operation_id,
                "amount": event.amount,
                "currency": event.currency,
                "raw_payload": event.raw_payload,
            },
        )

        # Integración contractual OFF-CHAIN
        contract_engine.on_participant_funded(
            session_id=event.session_id,
            user_id=event.user_id,
            amount=event.amount,
            fintech_operation_id=event.fintech_operation_id,
        )

    def mark_all_deposits_ok(self, session_id: str) -> None:
        """
        Llamado normalmente desde contract_engine cuando detecta
        que todos los depósitos requeridos están autorizados.
        """
        snapshot = self._load_payment_state(session_id)
        new_snapshot = PaymentStateMachine.transition(
            snapshot,
            PaymentEvent.ALL_DEPOSITS_OK,
        )
        self._save_payment_state(new_snapshot)

        self.audit_repo.log(
            action="ALL_DEPOSITS_OK",
            session_id=session_id,
            user_id=None,
            metadata={},
        )

    def handle_settlement_completed(
        self,
        event: SettlementCompletedEvent,
    ) -> None:
        """
        1. Actualiza estado a SETTLED.
        2. Auditoría.
        3. Notifica a contract_engine.on_settlement_completed.
        """
        snapshot = self._load_payment_state(event.session_id)

        snapshot.total_settled_amount = (snapshot.total_settled_amount or 0.0) + event.amount

        new_snapshot = PaymentStateMachine.transition(
            snapshot,
            PaymentEvent.SETTLEMENT_CONFIRMED,
        )
        self._save_payment_state(new_snapshot)

        self.audit_repo.log(
            action="SETTLEMENT_COMPLETED",
            session_id=event.session_id,
            user_id=None,
            metadata={
                "fintech_operation_id": event.fintech_operation_id,
                "provider_id": event.provider_id,
                "amount": event.amount,
                "currency": event.currency,
                "raw_payload": event.raw_payload,
            },
        )

        contract_engine.on_settlement_completed(
            session_id=event.session_id,
            provider_id=event.provider_id,
            amount=event.amount,
            fintech_operation_id=event.fintech_operation_id,
        )

    def handle_force_majeure_refund(
        self,
        event: ForceMajeureRefundEvent,
    ) -> None:
        """
        1. Lleva PaymentState a FORCE_MAJEURE (si no lo está).
        2. Auditoría.
        3. Notifica a contract_engine.on_force_majeure_refund.
        """
        snapshot = self._load_payment_state(event.session_id)

        new_snapshot = PaymentStateMachine.transition(
            snapshot,
            PaymentEvent.FORCE_MAJEURE_TRIGGERED,
        )
        self._save_payment_state(new_snapshot)

        self.audit_repo.log(
            action="FORCE_MAJEURE_REFUND",
            session_id=event.session_id,
            user_id=event.adjudicatario_user_id,
            metadata={
                "fintech_operation_id": event.fintech_operation_id,
                "amount_refunded": event.amount_refunded,
                "currency": event.currency,
                "raw_payload": event.raw_payload,
            },
        )

        contract_engine.on_force_majeure_refund(
            session_id=event.session_id,
            adjudicatario_user_id=event.adjudicatario_user_id,
            amount_refunded=event.amount_refunded,
            fintech_operation_id=event.fintech_operation_id,
        )
