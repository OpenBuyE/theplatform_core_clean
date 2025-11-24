# backend_core/services/participant_repository.py

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event

PARTICIPANTS_TABLE = "ca_session_participants"


# ============================================================
#  CREAR PARTICIPANTE (GENERAL)
# ============================================================

def add_participant(
    session_id: str,
    user_id: str,
    amount: float,
    price: float,
    quantity: int = 1,
    organization_id: Optional[str] = None,
) -> Dict:
    """
    Inserta un nuevo participante en la sesión.
    """

    data = {
        "session_id": session_id,
        "user_id": user_id,
        "amount": amount,
        "price": price,
        "quantity": quantity,
        "organization_id": organization_id,
        "is_awarded": False,
        "created_at": datetime.utcnow().isoformat(),
    }

    resp = table(PARTICIPANTS_TABLE).insert(data).execute()
    row = resp.data[0]

    log_event(
        "participant_added",
        session_id=session_id,
        user_id=user_id,
        metadata=data,
    )

    return row


# ============================================================
#  PARTICIPANTE DE TEST (USADO POR DASHBOARD)
# ============================================================

def add_test_participant(
    session_id: str,
    user_id: str = "test-user",
    amount: float = 1.0,
    price: float = 1.0,
    quantity: int = 1,
) -> Dict:
    """
    Crea un participante de prueba sin pasar por MangoPay.
    Esto se usa exclusivamente en el panel administrador.
    """

    return add_participant(
        session_id=session_id,
        user_id=user_id,
        amount=amount,
        price=price,
        quantity=quantity,
    )


# ============================================================
#  OBTENER PARTICIPANTES DE UNA SESIÓN
# ============================================================

def get_participants_for_session(session_id: str) -> List[Dict]:
    resp = (
        table(PARTICIPANTS_TABLE)
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )
    return resp.data or []


# ============================================================
#  MARCAR GANADOR / ADJUDICATARIO
# ============================================================

def mark_awarded(session_id: str, participant_id: str) -> None:
    """
    Marca un participante como adjudicatario.
    """

    resp = (
        table(PARTICIPANTS_TABLE)
        .update({"is_awarded": True})
        .eq("id", participant_id)
        .eq("session_id", session_id)
        .execute()
    )

    log_event(
        "participant_awarded",
        session_id=session_id,
        metadata={"participant_id": participant_id},
    )
