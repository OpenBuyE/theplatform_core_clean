"""
Domain Model: Participant
Entidad base asociada a una sesión.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, validator


class Participant(BaseModel):
    id: str
    session_id: str
    user_id: str
    organization_id: Optional[str]

    amount: float = 0
    price: float = 0
    quantity: int = 1

    is_awarded: bool = False
    awarded_at: Optional[str] = None
    created_at: Optional[str] = None

    @validator("quantity")
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("quantity must be > 0")
        return v

    @validator("amount")
    def validate_amount(cls, v):
        if v < 0:
            raise ValueError("amount cannot be negative")
        return v

    @validator("price")
    def validate_price(cls, v):
        if v < 0:
            raise ValueError("price cannot be negative")
        return v

    def award(self, ts: Optional[str] = None):
        self.is_awarded = True
        self.awarded_at = ts or datetime.utcnow().isoformat()
