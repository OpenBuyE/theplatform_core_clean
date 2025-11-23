# backend_core/services/payment_session_repository.py

from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import datetime

from backend_core.services import supabase_client


PAYMENT_TABLE = "ca_payment_sessions"


def create_payment_session(
    session_id: str,
    organization_id: str,
    expected_amount: float,
) -> Any:
    """
    Crea una PaymentSession recibiendo expected_amount desde ContractEngine.
    Nunca calcula valores ni usa defaults.
    """
    payload = {
        "session_id": session_id,
        "organization_id": organization_id,
        "total_expected_amount": expected_amount,
        "total_deposited_amount": 0.0,
        "created_at": datetime.utcnow().isoformat(),
        "status": "WAITING_DEPOSITS",
    }

    resp = supabase_client.table(PAYMENT_TABLE).insert(payload).execute()
    return resp.data[0]


def get_payment_session_by_session_id(session_id: str) -> Optional[Any]:
    resp = (
        supabase_client.table(PAYMENT_TABLE)
        .select("*")
        .eq("session_id", session_id)
        .single()
        .execute()
    )
    return resp.data


def update_payment_deposit(session_id: str, amount: float) -> None:
    """
    Suma depósitos sin calcular expected_amount. Solo incrementa deposited.
    """
    session = get_payment_session_by_session_id(session_id)
    if not session:
        return

    new_total = float(session["total_deposited_amount"] or 0.0) + float(amount)

    supabase_client.table(PAYMENT_TABLE).update(
        {"total_deposited_amount": new_total}
    ).eq("session_id", session_id).execute()


def mark_payment_settled(session_id: str) -> None:
    supabase_client.table(PAYMENT_TABLE).update(
        {"status": "SETTLED"}
    ).eq("session_id", session_id).execute()


def mark_force_majeure(session_id: str) -> None:
    supabase_client.table(PAYMENT_TABLE).update(
        {"status": "FORCE_MAJEURE"}
    ).eq("session_id", session_id).execute()
