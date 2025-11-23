# backend_core/models/payment_session.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel

from backend_core.models.payment_state import PaymentStatus


class PaymentSession(BaseModel):
    """
    Proyección de la fila de ca_payment_sessions.
    Es el agregado de pagos asociado a una ca_session.
    """

    id: str
    session_id: str
    organization_id: str

    status: PaymentStatus

    total_expected_amount: Optional[float] = None
    total_deposited_amount: Optional[float] = None
    total_settled_amount: Optional[float] = None

    force_majeure: bool = False

    created_at: datetime
    updated_at: datetime

    metadata: Dict[str, Any] = {}
