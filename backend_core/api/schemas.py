from pydantic import BaseModel
from typing import Optional, List


# ---------------------------------------------------------
# Session schemas
# ---------------------------------------------------------

class SessionBase(BaseModel):
    id: str
    product_id: str
    series_id: str
    sequence_number: int
    organization_id: str
    status: str
    capacity: int
    pax_registered: int
    activated_at: Optional[str]
    expires_at: Optional[str]
    finished_at: Optional[str]


class SessionList(BaseModel):
    sessions: List[SessionBase]


# ---------------------------------------------------------
# Participant schemas
# ---------------------------------------------------------

class ParticipantIn(BaseModel):
    user_id: str
    organization_id: str
    amount: float
    price: float
    quantity: int


class ParticipantOut(BaseModel):
    id: str
    session_id: str
    user_id: str
    organization_id: str
    amount: float
    price: float
    quantity: int
    created_at: str
    is_awarded: bool
    awarded_at: Optional[str]


class ParticipantsList(BaseModel):
    participants: List[ParticipantOut]


# ---------------------------------------------------------
# Seeds
# ---------------------------------------------------------

class SeedUpdate(BaseModel):
    public_seed: str


class SeedResponse(BaseModel):
    session_id: str
    public_seed: Optional[str]
