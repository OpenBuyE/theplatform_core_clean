"""
fintech_routes.py — versión conectada
-------------------------------------

Ahora estos endpoints:
- Registran auditoría
- Y activan directamente wallet_events → wallet_orchestrator
  → contract_engine
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from backend_core.services.audit_repository import log_event
from backend_core.services.wallet_events import wallet_events
from .deps import api_key_required


router = APIRouter(
    prefix="/fintech",
    tags=["fintech"],
    dependencies=[Depends(api_key_required)]
)


# =========================================================
# MODELOS Pydantic
# =========================================================

class DepositNotification(BaseModel):
    session_id: str
    participant_id: str
    amount: float
    currency: str = "EUR"
    fintech_tx_id: str
    status: str


class SettlementNotification(BaseModel):
    session_id: str
    adjudicatario_id: str
    fintech_batch_id: str
    status: str


class ForceMajeureRefund(BaseModel):
    session_id: str
    adjudicatario_id: str
    product_amount: float
    currency: str = "EUR"
    fintech_refund_tx_id: Optional[str] = None
    reason: Optional[str] = None


# =========================================================
# 1) Depósito OK
# =========================================================
@router.post("/deposit-ok")
def fintech_deposit_ok(payload: DepositNotification):

    log_event(
        action="fintech_deposit_ok",
        session_id=payload.session_id,
        user_id=payload.participant_id,
        metadata=payload.dict()
    )

    wallet_events.on_deposit_ok(
        session_id=payload.session_id,
        participant_id=payload.participant_id,
        amount=payload.amount,
        currency=payload.currency,
        fintech_tx_id=payload.fintech_tx_id,
        status=payload.status
    )

    return {"status": "ok"}


# =========================================================
# 2) Liquidación completada
# =========================================================
@router.post("/settlement")
def fintech_settlement(payload: SettlementNotification):

    log_event(
        action="fintech_settlement",
        session_id=payload.session_id,
        user_id=payload.adjudicatario_id,
        metadata=payload.dict()
    )

    wallet_events.on_settlement_completed(
        session_id=payload.session_id,
        adjudicatario_id=payload.adjudicatario_id,
        fintech_batch_id=payload.fintech_batch_id,
        status=payload.status
    )

    return {"status": "ok"}


# =========================================================
# 3) Fuerza mayor (devolución del producto)
# =========================================================
@router.post("/force-majeure-refund")
def fintech_force_majeure_refund(payload: ForceMajeureRefund):

    log_event(
        action="fintech_force_majeure_refund",
        session_id=payload.session_id,
        user_id=payload.adjudicatario_id,
        metadata=payload.dict()
    )

    wallet_events.on_force_majeure_refund(
        session_id=payload.session_id,
        adjudicatario_id=payload.adjudicatario_id,
        product_amount=payload.product_amount,
        currency=payload.currency,
        fintech_refund_tx_id=payload.fintech_refund_tx_id,
        reason=payload.reason
    )

    return {"status": "ok"}
