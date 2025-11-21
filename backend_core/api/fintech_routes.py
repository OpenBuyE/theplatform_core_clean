"""
fintech_routes.py
Endpoints REST relacionados con la Fintech / pasarela de pago.

Objetivo (versión 1, segura y mínima):
- Recibir notificaciones de la Fintech (webhooks simulados).
- Delegar la lógica a wallet_orchestrator.
- Registrar todo en audit_logs vía wallet_events.

Más adelante:
- wallet_orchestrator hablará con contract_engine para cerrar
  el ciclo completo (depósito OK, liquidación, fuerza mayor, etc.).
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from .deps import api_key_required
from backend_core.services.wallet_orchestrator import wallet_orchestrator


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

    Flujo:
    - Validación básica por FastAPI (pydantic).
    - Delegación a wallet_orchestrator.handle_deposit_ok().
    - Registro en audit_logs vía wallet_events.
    """

    wallet_orchestrator.handle_deposit_ok(payload.dict())
    return {"status": "ok", "message": "Deposit notification processed"}


# ---------------------------------------------------------
# 2) Notificación de liquidación (pago al proveedor + OÜ + DMHG)
# ---------------------------------------------------------

@router.post("/settlement")
def fintech_settlement(payload: SettlementNotification):
    """
    Endpoint llamado cuando la Fintech ha ejecutado la liquidación
    de una sesión ya adjudicada.
    """

    wallet_orchestrator.handle_settlement(payload.dict())
    return {"status": "ok", "message": "Settlement notification processed"}


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

    wallet_orchestrator.handle_force_majeure_refund(payload.dict())
    return {"status": "ok", "message": "Force majeure refund processed"}
