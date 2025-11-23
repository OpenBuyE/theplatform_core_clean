from __future__ import annotations

from datetime import datetime
from typing import Optional

from backend_core.services import supabase_client
from backend_core.models.payment_session import PaymentSession
from backend_core.models.payment_state import PaymentStatus


def create_payment_session(
    session_id: str,
    organization_id: str,
    expected_amount: float,
) -> PaymentSession:
    payload = {
        "session_id": session_id,
        "organization_id": organization_id,
        "status": PaymentStatus.WAITING_DEPOSITS.value,
        "total_expected_amount": expected_amount,
        "total_deposited_amount": 0.0,
        "total_settled_amount": 0.0,
        "force_majeure": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "metadata": {},
    }

    resp = supabase_client.table("ca_payment_sessions").insert(payload).execute()
    row = resp.data[0]
    return PaymentSession(**row)


def get_payment_session(session_id: str) -> Optional[PaymentSession]:
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


def update_payment_session_status(
    session_id: str,
    new_status: PaymentStatus,
) -> None:
    supabase_client.table("ca_payment_sessions").update(
        {
            "status": new_status.value,
            "updated_at": datetime.utcnow().isoformat(),
        }
    ).eq("session_id", session_id).execute()
