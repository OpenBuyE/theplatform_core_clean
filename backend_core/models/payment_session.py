from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel
from backend_core.models.payment_state import PaymentStatus


class PaymentSession(BaseModel):
    id: str
    session_id: str
    organization_id: str

    status: PaymentStatus
    total_expected_amount: Optional[float]
    total_deposited_amount: Optional[float]
    total_settled_amount: Optional[float]

    force_majeure: bool = False
    created_at: datetime
    updated_at: datetime

    metadata: Dict[str, Any] = {}
