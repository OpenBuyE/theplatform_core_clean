# backend_core/services/contract_engine.py
from __future__ import annotations

from backend_core.services import supabase_client
from backend_core.services.payment_session_repository import (
    create_payment_session,
    get_payment_session_by_session_id,
)
from backend_core.services.audit_repository import AuditRepository

audit_repo = AuditRepository()


def on_session_awarded(session_id: str, adjudicatario_user_id: str) -> None:
    """
    Llamado desde adjudicator_engine cuando existe adjudicatario.
    Aquí comienza formalmente el flujo de pagos.
    """

    # 1. Recuperar datos relevantes de la sesión
    resp = (
        supabase_client.table("ca_sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )
    session = resp.data

    if not session:
        raise ValueError(f"Session {session_id} not found")

    organization_id = session["organization_id"]

    # expected_amount = precio * nº participantes
    # Ajusta según tu modelo real (p.ej. field price en productos_v2)
    price = float(session.get("price", 0))
    capacity = float(session.get("capacity", 0))
    expected_amount = price * capacity

    # 2. Evitar duplicados
    existing = get_payment_session_by_session_id(session_id)
    if not existing:
        create_payment_session(
            session_id=session_id,
            organization_id=organization_id,
            expected_amount=expected_amount,
        )

        audit_repo.log(
            action="PAYMENT_SESSION_CREATED",
            session_id=session_id,
            user_id=adjudicatario_user_id,
            metadata={
                "expected_amount": expected_amount,
                "price": price,
                "capacity": capacity,
            },
        )

    else:
        # Ya existe → solo auditoría informativa
        audit_repo.log(
            action="PAYMENT_SESSION_ALREADY_EXISTS",
            session_id=session_id,
            user_id=adjudicatario_user_id,
        )
