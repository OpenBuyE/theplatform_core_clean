"""
Domain Model: Adjudication Seed
Representa una semilla determinista asociada a una sesión.
"""

from pydantic import BaseModel
from typing import Optional


class AdjudicationSeed(BaseModel):
    session_id: str
    public_seed: Optional[str] = None

    def effective_seed(self) -> str:
        return self.public_seed or ""
