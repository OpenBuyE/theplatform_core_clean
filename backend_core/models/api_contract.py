# backend_core/models/api_contract.py
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel

from backend_core.models.contract_session import ContractSession
from backend_core.models.payment_session import PaymentSession


class ContractFullView(BaseModel):
    """
    Vista completa del estado contractual.
    """
    contract: Optional[ContractSession]
    payment_session: Optional[PaymentSession]
    session: dict  # datos crudos de ca_sessions (para contexto)


class ContractViewResponse(BaseModel):
    status: str = "ok"
    data: ContractFullView
