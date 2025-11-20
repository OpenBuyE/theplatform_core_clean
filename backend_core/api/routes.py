from fastapi import APIRouter, HTTPException, Depends
from typing import List

from .schemas import (
    ParticipantIn, ParticipantOut, ParticipantsList,
    SessionBase, SessionList,
    SeedUpdate, SeedResponse
)

# Servicios
from backend_core.services.session_repository import session_repository
from backend_core.services.participant_repository import participant_repository
from backend_core.services.adjudicator_repository import adjudicator_repository
from backend_core.services.adjudicator_engine import adjudicator_engine
from backend_core.services.session_engine import session_engine

# Dependencias
from .deps import api_key_required


router = APIRouter()


# ============================================================
#  SESSIONS
# ============================================================

@router.get("/sessions", response_model=SessionList, dependencies=[Depends(api_key_required)])
def list_sessions():
    sessions = session_repository.get_sessions(limit=500)
    return {"sessions": sessions}


@router.get("/sessions/{session_id}", response_model=SessionBase, dependencies=[Depends(api_key_required)])
def get_session(session_id: str):
    session = session_repository.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# ============================================================
#  PARTICIPANTS
# ============================================================

@router.post("/sessions/{session_id}/participants", response_model=ParticipantOut, dependencies=[Depends(api_key_required)])
def add_participant(session_id: str, payload: ParticipantIn):
    participant = participant_repository.add_participant(
        session_id=session_id,
        user_id=payload.user_id,
        organization_id=payload.organization_id,
        amount=payload.amount,
        price=payload.price,
        quantity=payload.quantity
    )

    if not participant:
        raise HTTPException(status_code=400, detail="Could not add participant")

    return participant


@router.get("/sessions/{session_id}/participants", response_model=ParticipantsList, dependencies=[Depends(api_key_required)])
def list_participants(session_id: str):
    parts = participant_repository.get_participants_by_session(session_id)
    return {"participants": parts}


# ============================================================
#  SEEDS
# ============================================================

@router.get("/sessions/{session_id}/seed", response_model=SeedResponse, dependencies=[Depends(api_key_required)])
def get_seed(session_id: str):
    seed = adjudicator_repository.get_public_seed_for_session(session_id)
    return {"session_id": session_id, "public_seed": seed}


@router.post("/sessions/{session_id}/seed", dependencies=[Depends(api_key_required)])
def set_seed(session_id: str, payload: SeedUpdate):
    adjudicator_repository.set_public_seed_for_session(session_id, payload.public_seed)
    return {"status": "ok"}


@router.delete("/sessions/{session_id}/seed", dependencies=[Depends(api_key_required)])
def delete_seed(session_id: str):
    adjudicator_repository.delete_seed_for_session(session_id)
    return {"status": "deleted"}


# ============================================================
#  ADJUDICATION (DEV ONLY)
# ============================================================

@router.post("/adjudicate/{session_id}", dependencies=[Depends(api_key_required)])
def adjudicate_manual(session_id: str):
    result = adjudicator_engine.adjudicate_session(session_id)
    if not result:
        raise HTTPException(status_code=400, detail="Adjudication failed")
    return {"winner": result}


# ============================================================
#  EXPIRATION PROCESS (DEV ONLY)
# ============================================================

@router.post("/engine/expire", dependencies=[Depends(api_key_required)])
def run_expiration_now():
    session_engine.process_expired_sessions()
    return {"status": "expiration_executed"}


# ============================================================
#  ROLLING: ACTIVATE NEXT SESSION
# ============================================================

@router.post("/engine/rolling/{session_id}", dependencies=[Depends(api_key_required)])
def activate_next(session_id: str):
    session = session_repository.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    next_active = session_engine.activate_next_session_in_series(session)
    return {"activated": next_active}
