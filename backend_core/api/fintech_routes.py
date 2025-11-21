"""
fintech_routes.py
Endpoints REST relacionados con la Fintech / pasarela de pago.

Objetivo (versión 1, segura y mínima):
- Recibir notificaciones de la Fintech (webhooks simulados).
- Registrar todo en audit_logs para trazabilidad.
- No acoplar todavía a wallet_orchestrator / contract_engine
  hasta tenerlos totalmente estabilizados.

Más adelante:
- Estos endpoints llamarán a wallet_orchestrator y contract_engine
  para cerrar el ciclo completo (depósito OK, liquidación, fuerza mayor, etc.).
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any

from backend_core.services.audit_repository import log_event
from .deps import api_key_required

router = APIRouter(
    prefix="/fintech",
    tags=["fintech"],
    dependencies=[Depends(api_key_required)],
)


# ---------------------------------------------------------
# Modelos de entrada (payloads Fintech / internos)
# ---------------------------------------------------------

class DepositNotification(BaseModel):
    """
    Notificación de que un depósito (pago del participante)
    ha sido AUTORIZADO y bloqueado en la Fintech.
    """
    session_id: str
    participant_id: str
    amount: float
    currency: str = "EUR"
    fintech_tx_id: str
    status: str  # ejemplo: "AUTHORIZED", "FAILED", ...


class SettlementNotification(BaseModel):
    """
    Notificación de que la Fintech ha ejecutado la liquidación:
    - Pago al proveedor
    - Comisiones / gastos de gestión
    """
    session_id: str
    adjudicatario_id: str
    fintech_batch_id: str
    status: str  # ejemplo: "SETTLED", "FAILED", ...


class ForceMajeureRefund(BaseModel):
    """
    Notificación/cmd de caso de fuerza mayor:
    - No se puede entregar el producto.
    - Se devuelve al adjudicatario SOLO el precio del producto.
    """
    session_id: str
    adjudicatario_id: str
    product_amount: float
    currency: str = "EUR"
    fintech_refund_tx_id: Optional[str] = None
    reason: Optional[str] = None


# ---------------------------------------------------------
# 1) Notificación de depósito OK (webhook Fintech)
# ---------------------------------------------------------

@router.post("/deposit-ok")
def fintech_deposit_ok(payload: DepositNotification):
    """
    Endpoint llamado por la Fintech (o por nuestro backend intermedio)
    cuando un depósito de un participante ha sido AUTORIZADO.

    Versión 1:
    - Solo registra el evento en auditoría.
    - Más adelante: llamará a wallet_orchestrator/contract_engine.
    """

    log_event(
        action="fintech_deposit_ok",
        session_id=payload.session_id,
        user_id=payload.participant_id,
        metadata={
            "amount": payload.amount,
            "currency": payload.currency,
            "fintech_tx_id": payload.fintech_tx_id,
            "status": payload.status,
        }
    )

    # Aquí en el futuro:
    # - wallet_orchestrator.on_deposit_ok(...)
    # - contract_engine.on_participant_funded(...)

    return {"status": "ok", "message": "Deposit notification received"}


# ---------------------------------------------------------
# 2) Notificación de liquidación (pago al proveedor + OÜ + DMHG)
# ---------------------------------------------------------

@router.post("/settlement")
def fintech_settlement(payload: SettlementNotification):
    """
    Endpoint llamado cuando la Fintech ha ejecutado la liquidación
    de una sesión ya adjudicada.
    """

    log_event(
        action="fintech_settlement",
        session_id=payload.session_id,
        user_id=payload.adjudicatario_id,
        metadata={
            "fintech_batch_id": payload.fintech_batch_id,
            "status": payload.status,
        }
    )

    # Futuro:
    # - contract_engine.on_settlement_completed(...)
    # - wallet_orchestrator.on_settlement_completed(...)

    return {"status": "ok", "message": "Settlement notification received"}


# ---------------------------------------------------------
# 3) Caso de fuerza mayor (devolución precio del producto)
# ---------------------------------------------------------

@router.post("/force-majeure-refund")
def fintech_force_majeure_refund(payload: ForceMajeureRefund):
    """
    Endpoint para gestionar el caso excepcional:
    - El proveedor NO puede entregar el producto.
    - La Fintech devuelve al adjudicatario SOLO el precio del producto.

    Importante:
    - NO se devuelven comisiones ni gastos de gestión.
    """

    log_event(
        action="fintech_force_majeure_refund",
        session_id=payload.session_id,
        user_id=payload.adjudicatario_id,
        metadata={
            "product_amount": payload.product_amount,
            "currency": payload.currency,
            "fintech_refund_tx_id": payload.fintech_refund_tx_id,
            "reason": payload.reason,
        }
    )

    # Futuro:
    # - contract_engine.on_force_majeure_refund(...)
    # - wallet_orchestrator.on_force_majeure_refund(...)

    return {"status": "ok", "message": "Force majeure refund recorded"}
