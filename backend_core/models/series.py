"""
Domain Model: Session Series
Representa un canal de rolling sessions.
"""

from pydantic import BaseModel
from typing import Optional


class SessionSeries(BaseModel):
    id: str
    organization_id: str
    product_id: str
    created_at: Optional[str] = None

    def describe(self):
        return f"Series({self.id}) for product {self.product_id}"
