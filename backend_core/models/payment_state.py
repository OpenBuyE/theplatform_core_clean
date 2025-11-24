# backend_core/models/payment_state.py

from __future__ import annotations

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel


# ============================================================
# ENUM OFICIAL — Payment State Machine
# ============================================================

class PaymentStateEnum(str, Enum):
    WAITING_DEPOSITS = "WAITING_DEPOSITS"
    DEPOSITS_OK = "DEPOSITS_OK"
    WAITING_SETTLEMENT = "WAITING_SETTLEMENT"
    SETTLED = "SETTLED"
    FORCE_MAJEURE = "FORCE_MAJEURE"


# ============================================================
# DOMAIN MODEL OFICIAL — PaymentSession
# ============================================================

class PaymentSession(BaseModel):
    session_id: str
    status: PaymentStateEnum
    awarded_participant_id: Optional[str] = None
    total_deposited_amount: Optional[float] = 0.0
    total_required_amount: Optional[float] = 0.0
    mangopay_wallet_id: Optional[str] = None
    mangopay_transfer_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True

    def to_dict(self) -> Dict[str, Any]:
        """Compatibilidad total con repositorios, engines y vistas."""
        return self.dict()
