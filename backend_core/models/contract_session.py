# backend_core/models/contract_session.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel

"""
Este modelo representa el expediente contractual completo
de una sesión adjudicada dentro de Compra Abierta.
Se corresponde con la tabla ca_contract_sessions.
"""

class ContractStatus:
    CREATED = "CREATED"
    WAITING_DEPOSITS = "WAITING_DEPOSITS"
    GROUP_FUNDED = "GROUP_FUNDED"
    WAITING_SETTLEMENT = "WAITING_SETTLEMENT"
    PROVIDER_PAID = "PROVIDER_PAID"
    DELIVERED = "DELIVERED"
    CLOSED = "CLOSED"
    FORCE_MAJEURE = "FORCE_MAJEURE"
    REFUNDED = "REFUNDED"

    ALL = {
        CREATED,
        WAITING_DEPOSITS,
        GROUP_FUNDED,
        WAITING_SETTLEMENT,
        PROVIDER_PAID,
        DELIVERED,
        CLOSED,
        FORCE_MAJEURE,
        REFUNDED,
    }


class ContractSession(BaseModel):
    """
    Modelo completo del contrato de compra colectiva.
    Este expediente engloba:
    - adjudicación determinista
    - flujo de pagos (sin tocar dinero)
    - settlement con proveedor
    - fuerza mayor
    - entrega
    - cierre del contrato

    Es la vista oficial y auditable del ciclo contractual.
    """

    id: str
    session_id: str
    payment_session_id: Optional[str]

    adjudicatario_user_id: str
    organization_id: str
    provider_id: Optional[str]
    product_id: Optional[str]

    status: str

    created_at: datetime
    updated_at: datetime

    # -- timestamps del ciclo contractual --
    awarded_at: Optional[datetime]
    deposits_completed_at: Optional[datetime]
    settlement_requested_at: Optional[datetime]
    provider_paid_at: Optional[datetime]
    delivered_at: Optional[datetime]
    closed_at: Optional[datetime]
    force_majeure_at: Optional[datetime]
    refunded_at: Optional[datetime]

    # -- información de entrega --
    delivery_method: Optional[str]  # store_pickup | shipment | warehouse
    delivery_location: Optional[str]
    delivery_metadata: Dict[str, Any] = {}

    # -- metadata general --
    metadata: Dict[str, Any] = {}

    class Config:
        orm_mode = True
