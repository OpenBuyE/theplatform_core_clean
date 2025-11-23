# backend_core/services/payment_state_machine.py

from __future__ import annotations
from typing import Optional
from backend_core.models.payment_state import PaymentStateEnum
from backend_core.services.payment_session_repository import (
    get_payment_session_by_session_id,
    mark_payment_settled,
    mark_force_majeure,
)


def evaluate_payment_state(session_id: str) -> Optional[PaymentStateEnum]:
    """
    La máquina de estados de pago evalúa el estado actual sin calcular expected_amount.
    Solo compara 'total_expected_amount' y 'total_deposited_amount'.
    """
    session = get_payment_session_by_session_id(session_id)
    if not session:
        return None

    expected = float(session["total_expected_amount"] or 0.0)
    deposited = float(session["total_deposited_amount"] or 0.0)
    status = session.get("status")

    # GROUP FUNDED (todos los depósitos completados)
    if deposited >= expected > 0:
        return PaymentStateEnum.DEPOSITS_OK

    # Estados especiales
    if status == "SETTLED":
        return PaymentStateEnum.SETTLED

    if status == "FORCE_MAJEURE":
        return PaymentStateEnum.FORCE_MAJEURE

    return PaymentStateEnum.WAITING_DEPOSITS


def mark_settlement(session_id: str) -> None:
    mark_payment_settled(session_id)


def mark_force_majeure_refund(session_id: str) -> None:
    mark_force_majeure(session_id)
