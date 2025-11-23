# backend_core/api/fintech_routes.py
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Request, status

from backend_core.api.deps import get_wallet_orchestrator
from backend_core.services.wallet_orchestrator import WalletOrchestrator
from backend_core.services.wallet_events import (
    DepositOkEvent,
    SettlementCompletedEvent,
    ForceMajeureRefundEvent,
)

router = APIRouter(prefix="/fintech", tags=["fintech"])


@router.post("/deposit-ok", status_code=status.HTTP_200_OK)
async def deposit_ok(
    request: Request,
    orchestrator: WalletOrchestrator = Depends(get_wallet_orchestrator),
):
    """
    Webhook: confirmación de depósito autorizado por la Fintech.
    El payload (ejemplo) podría ser:
    {
        "operation_id": "fintx_123",
        "session_id": "uuid-session",
        "user_id": "user-123",
        "amount": 25.0,
        "currency": "EUR",
        ...
    }
    """
    payload = await request.json()

    event = DepositOkEvent(
        fintech_operation_id=payload["operation_id"],
        session_id=payload["session_id"],
        user_id=payload["user_id"],
        amount=float(payload["amount"]),
        currency=payload.get("currency", "EUR"),
        raw_payload=payload,
        received_at=datetime.utcnow(),
    )

    orchestrator.handle_deposit_ok(event)
    return {"status": "ok"}


@router.post("/settlement", status_code=status.HTTP_200_OK)
async def settlement(
    request: Request,
    orchestrator: WalletOrchestrator = Depends(get_wallet_orchestrator),
):
    """
    Webhook: confirmación de pago al proveedor.
    Payload (ejemplo):
    {
        "operation_id": "finset_456",
        "session_id": "uuid-session",
        "provider_id": "prov-789",
        "amount": 100.0,
        "currency": "EUR",
        ...
    }
    """
    payload = await request.json()

    event = SettlementCompletedEvent(
        fintech_operation_id=payload["operation_id"],
        session_id=payload["session_id"],
        provider_id=payload["provider_id"],
        amount=float(payload["amount"]),
        currency=payload.get("currency", "EUR"),
        raw_payload=payload,
        received_at=datetime.utcnow(),
    )

    orchestrator.handle_settlement_completed(event)
    return {"status": "ok"}


@router.post("/force-majeure-refund", status_code=status.HTTP_200_OK)
async def force_majeure_refund(
    request: Request,
    orchestrator: WalletOrchestrator = Depends(get_wallet_orchestrator),
):
    """
    Webhook: reembolso por fuerza mayor.
    Payload (ejemplo):
    {
        "operation_id": "finfm_789",
        "session_id": "uuid-session",
        "adjudicatario_user_id": "user-999",
        "amount_refunded": 80.0,
        "currency": "EUR",
        ...
    }
    """
    payload = await request.json()

    event = ForceMajeureRefundEvent(
        fintech_operation_id=payload["operation_id"],
        session_id=payload["session_id"],
        adjudicatario_user_id=payload["adjudicatario_user_id"],
        amount_refunded=float(payload["amount_refunded"]),
        currency=payload.get("currency", "EUR"),
        raw_payload=payload,
        received_at=datetime.utcnow(),
    )

    orchestrator.handle_force_majeure_refund(event)
    return {"status": "ok"}
