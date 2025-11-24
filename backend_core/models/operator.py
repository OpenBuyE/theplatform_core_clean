# backend_core/models/operator.py

from __future__ import annotations

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel


class OperatorKycStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    VALIDATED = "validated"
    REJECTED = "rejected"


class Operator(BaseModel):
    """
    Representa un operador (organización) integrado en la plataforma,
    con sus identificadores MangoPay y estado KYC/KYB.
    """
    id: str
    organization_id: str
    name: str

    mangopay_legal_user_id: Optional[str]
    mangopay_wallet_id: Optional[str]

    kyc_status: OperatorKycStatus = OperatorKycStatus.PENDING
    kyc_level: Optional[str]

    country: Optional[str]
    legal_person_type: Optional[str]

    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class OperatorKycLog(BaseModel):
    """
    Evento individual de KYC/KYB del operador,
    usado para auditoría detallada.
    """
    id: str
    operator_id: str

    event_type: str
    mangopay_kyc_id: Optional[str]
    status: Optional[str]
    payload: Dict[str, Any]

    created_at: datetime

    class Config:
        orm_mode = True
