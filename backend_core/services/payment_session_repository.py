# backend_core/services/payment_session_repository.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from backend_core.services import supabase_client
from backend_core.models.payment_session import PaymentSession
from backend_core.models.payment_state import (
    PaymentStatus,
    PaymentStateSnapshot,
)


def create_payment_session(
    session_id: str,
    organization_id: str,
    expected_amount: float,
) -> PaymentSession:
    """
    Crea la fila en ca_payment_sessions con estado inicial WAITING_DEPOSITS.
    Debe llamarse típicamente desde contract_engine.on_session_awarded.
    """
    now = datetime.utcnow().isoformat()

    payload = {
        "session_id": session_id,
        "organization_id": organization_id,
        "status": PaymentStatus.WAITING_DEPOSITS.value,
        "total_expected_amount": expected_amount,
        "total_deposited_amount": 0.0,
        "total_settled_amount": 0.0,
        "force_majeure": False,
        "metadata": {},
        "created_at": now,
        "updated_at": now,
    }

    resp = supabase_client.table("ca_payment_sessions").insert(payload).execute()
    row = resp.data[0]
    return PaymentSession(**row)


def get_payment_session_by_session_id(
    session_id: str,
) -> Optional[PaymentSession]:
    """
    Recupera la payment_session asociada a una sesión de compra.
    """
    resp = (
        supabase_client.table("ca_payment_sessions")
        .select("*")
        .eq("session_id", session_id)
        .single()
        .execute()
    )

    if not resp.data:
        return None

    return PaymentSession(**resp.data)


def save_payment_session(ps: PaymentSession) -> None:
    """
    Persiste los cambios de un PaymentSession (por id).
    No cambia created_at.
    """
    supabase_client.table("ca_payment_sessions").update(
        {
            "status": ps.status.value,
            "total_expected_amount": ps.total_expected_amount,
            "total_deposited_amount": ps.total_deposited_amount,
            "total_settled_amount": ps.total_settled_amount,
            "force_majeure": ps.force_majeure,
            "metadata": ps.metadata,
            "updated_at": datetime.utcnow().isoformat(),
        }
    ).eq("id", ps.id).execute()


def to_state_snapshot(ps: PaymentSession) -> PaymentStateSnapshot:
    """
    Convierte un PaymentSession a PaymentStateSnapshot para la state machine.
    """
    return PaymentStateSnapshot(
        payment_session_id=ps.id,
        session_id=ps.session_id,
        status=ps.status,
        total_expected_amount=ps.total_expected_amount,
        total_deposited_amount=ps.total_deposited_amount,
        total_settled_amount=ps.total_settled_amount,
        force_majeure=ps.force_majeure,
        updated_at=ps.updated_at,
        metadata=ps.metadata,
    )
