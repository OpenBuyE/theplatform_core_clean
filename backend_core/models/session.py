"""
Domain Model: Session
Entidad base del motor de Compra Abierta.
Representa una sesión de compra colectiva en cualquier estado:
parked → active → finished
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, validator


class Session(BaseModel):
    id: str
    product_id: str
    organization_id: str
    series_id: str
    sequence_number: int

    status: str  # parked | active | finished
    capacity: int
    pax_registered: int = 0

    activated_at: Optional[str] = None
    expires_at: Optional[str] = None
    finished_at: Optional[str] = None
    created_at: Optional[str] = None

    # -------------------------------
    # VALIDACIONES
    # -------------------------------
    @validator("capacity")
    def validate_capacity(cls, v):
        if v <= 0:
            raise ValueError("capacity must be > 0")
        return v

    @validator("pax_registered")
    def validate_pax(cls, v, values):
        if v < 0:
            raise ValueError("pax_registered cannot be negative")
        return v

    @validator("status")
    def validate_status(cls, v):
        allowed = {"parked", "active", "finished"}
        if v not in allowed:
            raise ValueError(f"Invalid session status: {v}")
        return v

    # -------------------------------
    # COMPORTAMIENTO DEL DOMINIO
    # -------------------------------
    def is_active(self) -> bool:
        return self.status == "active"

    def is_full(self) -> bool:
        return self.pax_registered >= self.capacity

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        now = datetime.utcnow().isoformat()
        return self.expires_at < now

    def can_accept_participant(self) -> bool:
        return self.is_active() and not self.is_full() and not self.is_expired()

    def mark_finished(self, ts: Optional[str] = None):
        self.status = "finished"
        self.finished_at = ts or datetime.utcnow().isoformat()
