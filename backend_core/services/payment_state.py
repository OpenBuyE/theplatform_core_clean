# backend_core/models/payment_state.py

from __future__ import annotations
from pydantic import BaseModel
from enum import Enum
from typing import Optional


class PaymentStateEnum(str, Enum):
    WAITING_DEPOSITS = "WAITING_DEPOSITS"
    DEPOSITS_OK = "DEPOSITS_OK"
    WAITING_SETTLEMENT = "WAITING_SETTLEMENT"
    SETTLED = "SETTLED"
    FORCE_MAJEURE = "FORCE_MAJEURE"


class PaymentSession(BaseModel):
    id: str
    session_id: str
    organization_id: str

    total_expected_amount: float
    total_deposited_amount: float

    status: PaymentStateEnum

    created_at: Optional[str] = None
