# backend_core/models/payment_state.py
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class PaymentStatus(str, Enum):
    """
    Estado AGREGADO del flujo de pagos de una sesión de compra colectiva.
    Se aplica a la 'payment_session' asociada a una ca_session.
    """
    WAITING_DEPOSITS = "WAITING_DEPOSITS"
    DEPOSITS_OK = "DEPOSITS_OK"
    WAITING_SETTLEMENT = "WAITING_SETTLEMENT"
    SETTLED = "SETTLED"
    FORCE_MAJEURE = "FORCE_MAJEURE"


class PaymentEvent(str, Enum):
    """
    Eventos que disparan transiciones de estado.
    Generados por:
    - Webhooks Fintech
    - Contract Engine
    - Lógica interna de negocio
    """
    PARTICIPANT_DEPOSIT_AUTHORIZED = "PARTICIPANT_DEPOSIT_AUTHORIZED"
    ALL_DEPOSITS_OK = "ALL_DEPOSITS_OK"
    ADJUDICATION_COMPLETED = "ADJUDICATION_COMPLETED"
    SETTLEMENT_REQUESTED = "SETTLEMENT_REQUESTED"
    SETTLEMENT_CONFIRMED = "SETTLEMENT_CONFIRMED"
    FORCE_MAJEURE_TRIGGERED = "FORCE_MAJEURE_TRIGGERED"
    FORCE_MAJEURE_REFUNDED = "FORCE_MAJEURE_REFUNDED"


class PaymentStateSnapshot(BaseModel):
    """
    Proyección en memoria del estado de pagos de una sesión.
    Ideal para:
    - state machine pura
    - test unitarios
    """
    payment_session_id: str
    session_id: str
    status: PaymentStatus
    total_expected_amount: Optional[float] = None
    total_deposited_amount: Optional[float] = None
    total_settled_amount: Optional[float] = None
    force_majeure: bool = False
    updated_at: datetime
    metadata: Dict[str, Any] = {}
