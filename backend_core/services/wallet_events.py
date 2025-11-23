# backend_core/services/wallet_events.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DepositOkEvent(BaseModel):
    """
    Webhook recibido cuando MangoPay confirma que un depósito
    (pago del comprador) ha sido autorizado / capturado.
    """
    fintech_operation_id: str = Field(..., alias="operation_id")
    session_id: str
    user_id: str
    amount: float
    currency: str
    raw_payload: Dict[str, Any]
    received_at: datetime


class SettlementCompletedEvent(BaseModel):
    """
    Webhook de confirmación de pago al proveedor.
    """
    fintech_operation_id: str = Field(..., alias="operation_id")
    session_id: str
    provider_id: str
    amount: float
    currency: str
    raw_payload: Dict[str, Any]
    received_at: datetime


class ForceMajeureRefundEvent(BaseModel):
    """
    Webhook de reembolso por fuerza mayor.
    IMPORTANTE: solo devuelve precio producto, no fees ni comisiones.
    """
    fintech_operation_id: str = Field(..., alias="operation_id")
    session_id: str
    adjudicatario_user_id: str
    amount_refunded: float
    currency: str
    raw_payload: Dict[str, Any]
    received_at: datetime

