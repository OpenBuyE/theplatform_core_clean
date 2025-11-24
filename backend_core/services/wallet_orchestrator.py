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
from backend_core.services.contract_engine import contract_engine
from backend_core.services.wallet_events import (
    DepositAuthorizedEvent,
    SettlementExecutedEvent,
    ForceMajeureRefundEvent,
)
from backend_core.services.session_repository import get_session_by_id
from backend_core.services.module_repository import get_session_module


audit = AuditRepository()


# ======================================================
# UTILIDAD: comprobar módulo
# ======================================================

def _check_module_allows_fintech(session_id: str) -> (bool, str):
    """
    Devuelve (allowed, module_code).
    Solo A_DETERMINISTIC puede procesar eventos fintech.
    """
    session = get_session_by_id(session_id)
    if not session:
        audit.log(
            action="FINTECH_EVENT_SESSION_NOT_FOUND",
            session_id=session_id,
            user_id=None,
            metadata={},
        )
        return False, "UNKNOWN"

    module = get_session_module(session)
    module_code = module["module_code"]

    if module_code != "A_DETERMINISTIC":
        audit.log(
            action="FINTECH_EVENT_BLOCKED_BY_MODULE",
            session_id=session_id,
            user_id=None,
            metadata={"module": module_code},
        )
        return False, module_code

    return True, module_code


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

    allowed, module_code = _check_module_allows_fintech(event.session_id)
    if not allowed:
        return {
            "handled": False,
            "blocked_by_module": module_code,
            "event": "deposit_authorized",
        }

    # 1) Actualizar PaymentSession (total_deposited_amount)
    update_payment_deposit(event.session_id, event.amount)

    # 2) Notificar al ContractEngine (DEPOSITS_OK)
    contract_engine.on_participant_funded(
        event.session_id,
        {
            "user_id": event.user_id,
            "amount": event.amount,
            "fintech_operation_id": event.fintech_operation_id,
        },
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
            "module": module_code,
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

    allowed, module_code = _check_module_allows_fintech(event.session_id)
    if not allowed:
        return {
            "handled": False,
            "blocked_by_module": module_code,
            "event": "settlement_executed",
        }

    # 1) Actualizar PaymentSession a SETTLED
    mark_settlement(event.session_id)

    # 2) Notificar al ContractEngine
    contract_engine.on_settlement_completed(
        event.session_id,
        {
            "provider_id": event.provider_id,
            "amount": event.amount,
            "fintech_operation_id": event.fintech_operation_id,
        },
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
            "module": module_code,
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

    allowed, module_code = _check_module_allows_fintech(event.session_id)
    if not allowed:
        return {
            "handled": False,
            "blocked_by_module": module_code,
            "event": "force_majeure_refund",
        }

    # 1) Actualizar PaymentSession a FORCE_MAJEURE
    mark_force_majeure_refund(event.session_id)

    # 2) Notificar ContractEngine
    contract_engine.on_force_majeure_refund(
        event.session_id,
        {
            "adjudicatario_user_id": event.adjudicatario_user_id,
            "amount_refunded": event.amount_refunded,
            "fintech_operation_id": event.fintech_operation_id,
        },
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
            "module": module_code,
        },
    )

    return {"handled": True, "event": "force_majeure_refund"}


# Solo para compatibilidad con imports existentes (no se usa directamente)
wallet_orchestrator = None
