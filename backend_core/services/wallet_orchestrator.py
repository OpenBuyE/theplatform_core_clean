# backend_core/services/wallet_orchestrator.py

from __future__ import annotations

from typing import Dict, Any

from backend_core.services.audit_repository import AuditRepository
from backend_core.services.payment_session_repository import (
    update_payment_deposit,
)
from backend_core.services.payment_state_machine import (
    mark_settlement,
    mark_force_majeure_refund,
)
from backend_core.services.contract_engine import (
    on_participant_funded,
    on_settlement_completed,
    on_force_majeure_refund,
)
from backend_core.services.wallet_events import (
    DepositAuthorizedEvent,
    SettlementExecutedEvent,
    ForceMajeureRefundEvent,
)


audit = AuditRepository()


# ======================================================
# 1) DEPÓSITO AUTORIZADO
# ======================================================

def handle_deposit_authorized(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orquesta un depósito confirmado por la Fintech.

    Espera un payload con al menos:
    - session_id
    - user_id
    - amount
    - fintech_operation_id
    """
    event = DepositAuthorizedEvent(
        session_id=payload["session_id"],
        user_id=payload["user_id"],
        amount=float(payload["amount"]),
        fintech_operation_id=payload["fintech_operation_id"],
        raw_payload=payload,
    )

    # 1) Actualizar PaymentSession (total_deposited_amount)
    update_payment_deposit(event.session_id, event.amount)

    # 2) Registrar evento en ContractEngine (puede disparar GROUP_FUNDED)
    on_participant_funded(
        session_id=event.session_id,
        user_id=event.user_id,
        amount=event.amount,
        fintech_operation_id=event.fintech_operation_id,
    )

    # 3) Auditoría
    audit.log(
        action="FINTECH_DEPOSIT_AUTHORIZED",
        session_id=event.session_id,
        user_id=event.user_id,
        metadata={
            "amount": event.amount,
            "fintech_operation_id": event.fintech_operation_id,
            "raw": event.raw_payload,
        },
    )

    return {"handled": True, "event": "deposit_authorized"}


# ======================================================
# 2) SETTLEMENT EJECUTADO
# ======================================================

def handle_settlement_executed(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orquesta un settlement (pago al proveedor) confirmado por la Fintech.

    Espera:
    - session_id
    - provider_id
    - amount
    - fintech_operation_id
    """
    event = SettlementExecutedEvent(
        session_id=payload["session_id"],
        provider_id=payload["provider_id"],
        amount=float(payload["amount"]),
        fintech_operation_id=payload["fintech_operation_id"],
        raw_payload=payload,
    )

    # 1) Actualizar PaymentSession a SETTLED
    mark_settlement(event.session_id)

    # 2) Notificar al ContractEngine
    on_settlement_completed(
        session_id=event.session_id,
        provider_id=event.provider_id,
        amount=event.amount,
        fintech_operation_id=event.fintech_operation_id,
    )

    # 3) Auditoría
    audit.log(
        action="FINTECH_SETTLEMENT_EXECUTED",
        session_id=event.session_id,
        user_id=None,
        metadata={
            "provider_id": event.provider_id,
            "amount": event.amount,
            "fintech_operation_id": event.fintech_operation_id,
            "raw": event.raw_payload,
        },
    )

    return {"handled": True, "event": "settlement_executed"}


# ======================================================
# 3) FORCE MAJEURE REFUND
# ======================================================

def handle_force_majeure_refund(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orquesta un reembolso por fuerza mayor.

    Espera:
    - session_id
    - adjudicatario_user_id
    - amount_refunded
    - fintech_operation_id
    """
    event = ForceMajeureRefundEvent(
        session_id=payload["session_id"],
        adjudicatario_user_id=payload["adjudicatario_user_id"],
        amount_refunded=float(payload["amount_refunded"]),
        fintech_operation_id=payload["fintech_operation_id"],
        raw_payload=payload,
    )

    # 1) Actualizar PaymentSession a FORCE_MAJEURE
    mark_force_majeure_refund(event.session_id)

    # 2) Notificar ContractEngine
    on_force_majeure_refund(
        session_id=event.session_id,
        adjudicatario_user_id=event.adjudicatario_user_id,
        amount_refunded=event.amount_refunded,
        fintech_operation_id=event.fintech_operation_id,
    )

    # 3) Auditoría
    audit.log(
        action="FINTECH_FORCE_MAJEURE_REFUND",
        session_id=event.session_id,
        user_id=event.adjudicatario_user_id,
        metadata={
            "amount_refunded": event.amount_refunded,
            "fintech_operation_id": event.fintech_operation_id,
            "raw": event.raw_payload,
        },
    )

    return {"handled": True, "event": "force_majeure_refund"}
