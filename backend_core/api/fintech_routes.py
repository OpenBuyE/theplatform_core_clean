# backend_core/api/fintech_routes.py

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from backend_core.services.wallet_orchestrator import (
    handle_deposit_authorized,
    handle_settlement_executed,
    handle_force_majeure_refund,
)
from backend_core.services.audit_repository import AuditRepository


router = APIRouter(prefix="/fintech", tags=["fintech"])

audit = AuditRepository()


# ======================================================
# /fintech/deposit-ok
# ======================================================

@router.post("/deposit-ok")
async def fintech_deposit_ok(request: Request):
    """
    Webhook que confirma un depósito de un participante.
    El payload esperado mínimo:
    {
        "session_id": "...",
        "user_id": "...",
        "amount": 25.0,
        "fintech_operation_id": "trx_123..."
    }
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON payload")

    if "session_id" not in payload or "user_id" not in payload:
        raise HTTPException(400, "Missing required fields")

    result = handle_deposit_authorized(payload)

    # Auditoría cruda de webhook recibido
    audit.log(
        action="FINTECH_WEBHOOK_DEPOSIT_OK",
        session_id=payload.get("session_id"),
        user_id=payload.get("user_id"),
        metadata=payload,
    )

    return {"status": "ok", "handled": result}


# ======================================================
# /fintech/settlement
# ======================================================

@router.post("/settlement")
async def fintech_settlement(request: Request):
    """
    Webhook que confirma el settlement al proveedor.
    Payload mínimo:
    {
        "session_id": "...",
        "provider_id": "...",
        "amount": 100.0,
        "fintech_operation_id": "settle_456..."
    }
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON payload")

    if "session_id" not in payload or "provider_id" not in payload:
        raise HTTPException(400, "Missing required fields")

    result = handle_settlement_executed(payload)

    audit.log(
        action="FINTECH_WEBHOOK_SETTLEMENT",
        session_id=payload.get("session_id"),
        user_id=None,
        metadata=payload,
    )

    return {"status": "ok", "handled": result}


# ======================================================
# /fintech/force-majeure-refund
# ======================================================

@router.post("/force-majeure-refund")
async def fintech_force_majeure_refund(request: Request):
    """
    Webhook que confirma un reembolso por fuerza mayor.
    Payload mínimo:
    {
        "session_id": "...",
        "adjudicatario_user_id": "...",
        "amount_refunded": 75.0,
        "fintech_operation_id": "refund_789..."
    }
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON payload")

    if "session_id" not in payload or "adjudicatario_user_id" not in payload:
        raise HTTPException(400, "Missing required fields")

    result = handle_force_majeure_refund(payload)

    audit.log(
        action="FINTECH_WEBHOOK_FORCE_MAJEURE",
        session_id=payload.get("session_id"),
        user_id=payload.get("adjudicatario_user_id"),
        metadata=payload,
    )

    return {"status": "ok", "handled": result}
