# backend_core/services/contract_engine.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from backend_core.services import supabase_client
from backend_core.services.audit_repository import AuditRepository

from backend_core.services.product_repository import get_product
from backend_core.services.payment_session_repository import (
    create_payment_session,
    get_payment_session_by_session_id,
)
from backend_core.services.contract_session_repository import (
    create_contract_session,
    get_contract_by_session_id,
    mark_deposits_completed,
    mark_settlement_requested,
    mark_provider_paid,
    mark_delivered,
    mark_closed,
    mark_force_majeure,
    mark_refunded,
    save_contract_session,
)

from backend_core.models.contract_session import ContractStatus

audit = AuditRepository()


# -------------------------------------------------------
# Helper interno para cargar la sesión
# -------------------------------------------------------

def _get_session_row(session_id: str) -> Dict[str, Any]:
    resp = (
        supabase_client.table("ca_sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )
    if not resp.data:
        raise ValueError(f"Session {session_id} not found")
    return resp.data



# ======================================================================
# 1) on_session_awarded
# ======================================================================

def on_session_awarded(session_id: str, adjudicatario_user_id: str) -> None:
    """
    Punto de entrada cuando el motor determinista produce un adjudicatario.

    - Obtiene producto real desde products_v2
    - Obtiene provider real desde products_v2
    - expected_amount = producto.price_final
    - Crea payment_session (WAITING_DEPOSITS)
    - Crea contract_session (WAITING_DEPOSITS)
    """

    session = _get_session_row(session_id)

    organization_id = session["organization_id"]
    product_id      = session.get("product_id")

    # ============================================================
    # 🟦 INTEGRACIÓN PRODUCTS_V2 AQUÍ (PASO 8.3)
    # ============================================================
    product = get_product(product_id)

    if not product:
        raise ValueError(f"No existe el producto products_v2 para session {session_id}")

    expected_amount = float(product["price_final"])
    provider_id     = product["provider_id"]
    # ============================================================

    # 1) PaymentSession
    payment_session = get_payment_session_by_session_id(session_id)

    if payment_session is None:
        payment_session = create_payment_session(
            session_id=session_id,
            organization_id=organization_id,
            expected_amount=expected_amount,
        )
        audit.log(
            action="PAYMENT_SESSION_CREATED",
            session_id=session_id,
            user_id=adjudicatario_user_id,
            metadata={"expected_amount": expected_amount},
        )
    else:
        audit.log(
            action="PAYMENT_SESSION_ALREADY_EXISTS",
            session_id=session_id,
            user_id=adjudicatario_user_id,
        )

    # 2) ContractSession
    contract = get_contract_by_session_id(session_id)

    if contract is None:
        contract = create_contract_session(
            session_id=session_id,
            payment_session_id=payment_session.id,
            adjudicatario_user_id=adjudicatario_user_id,
            organization_id=organization_id,
            provider_id=provider_id,
            product_id=product_id,
        )

        contract.status = ContractStatus.WAITING_DEPOSITS
        contract.awarded_at = datetime.utcnow()

        save_contract_session(contract)

        audit.log(
            action="CONTRACT_SESSION_CREATED",
            session_id=session_id,
            user_id=adjudicatario_user_id,
            metadata={
                "contract_id": contract.id,
                "payment_session_id": payment_session.id,
                "organization_id": organization_id,
                "provider_id": provider_id,
                "product_id": product_id,
                "expected_amount": expected_amount,
            },
        )
    else:
        audit.log(
            action="CONTRACT_SESSION_ALREADY_EXISTS",
            session_id=session_id,
            user_id=adjudicatario_user_id,
            metadata={"contract_id": contract.id},
        )



# ======================================================================
# 2) on_participant_funded
# ======================================================================

def on_participant_funded(
    session_id: str,
    user_id: str,
    amount: float,
    fintech_operation_id: str,
) -> None:

    audit.log(
        action="CONTRACT_PARTICIPANT_FUNDED",
        session_id=session_id,
        user_id=user_id,
        metadata={
            "amount": amount,
            "fintech_operation_id": fintech_operation_id,
        },
    )

    from backend_core.services.payment_session_repository import (
        get_payment_session_by_session_id,
    )

    payment_session = get_payment_session_by_session_id(session_id)

    if payment_session is None:
        return

    total_expected  = payment_session.total_expected_amount or 0.0
    total_deposited = payment_session.total_deposited_amount or 0.0

    if total_expected <= 0:
        return

    if total_deposited + 1e-9 < total_expected:
        return

    contract = get_contract_by_session_id(session_id)
    if contract is None:
        return

    if contract.status in (
        ContractStatus.CREATED,
        ContractStatus.WAITING_DEPOSITS,
    ):
        mark_deposits_completed(contract)
        audit.log(
            action="CONTRACT_GROUP_FUNDED",
            session_id=session_id,
            user_id=None,
            metadata={
                "total_expected": total_expected,
                "total_deposited": total_deposited,
            },
        )



# ======================================================================
# 3) on_settlement_requested
# ======================================================================

def on_settlement_requested(session_id: str, operator_user_id: Optional[str]) -> None:
    contract = get_contract_by_session_id(session_id)
    if contract is None:
        return

    if contract.status not in (
        ContractStatus.GROUP_FUNDED,
        ContractStatus.WAITING_SETTLEMENT,
    ):
        return

    mark_settlement_requested(contract)

    audit.log(
        action="CONTRACT_SETTLEMENT_REQUESTED",
        session_id=session_id,
        user_id=operator_user_id,
    )



# ======================================================================
# 4) on_settlement_completed
# ======================================================================

def on_settlement_completed(
    session_id: str,
    provider_id: str,
    amount: float,
    fintech_operation_id: str,
) -> None:

    contract = get_contract_by_session_id(session_id)
    if contract is None:
        return

    mark_provider_paid(contract)

    audit.log(
        action="CONTRACT_PROVIDER_PAID",
        session_id=session_id,
        user_id=None,
        metadata={
            "provider_id": provider_id,
            "amount": amount,
            "fintech_operation_id": fintech_operation_id,
        },
    )



# ======================================================================
# 5) on_delivery_confirmed
# ======================================================================

def on_delivery_confirmed(
    session_id: str,
    adjudicatario_user_id: str,
    delivery_method: Optional[str] = None,
    delivery_location: Optional[str] = None,
    delivery_metadata: Optional[Dict[str, Any]] = None,
) -> None:

    contract = get_contract_by_session_id(session_id)
    if contract is None:
        return

    if delivery_metadata is None:
        delivery_metadata = {}

    contract.delivery_method = delivery_method or contract.delivery_method
    contract.delivery_location = delivery_location or contract.delivery_location

    if delivery_metadata:
        contract.delivery_metadata.update(delivery_metadata)

    mark_delivered(contract)

    audit.log(
        action="CONTRACT_DELIVERY_CONFIRMED",
        session_id=session_id,
        user_id=adjudicatario_user_id,
        metadata={
            "delivery_method": delivery_method,
            "delivery_location": delivery_location,
            "delivery_metadata": delivery_metadata,
        },
    )



# ======================================================================
# 6) on_force_majeure_refund
# ======================================================================

def on_force_majeure_refund(
    session_id: str,
    adjudicatario_user_id: str,
    amount_refunded: float,
    fintech_operation_id: str,
) -> None:

    contract = get_contract_by_session_id(session_id)

    if contract is None:
        return

    mark_force_majeure(contract)
    mark_refunded(contract)

    audit.log(
        action="CONTRACT_FORCE_MAJEURE_REFUNDED",
        session_id=session_id,
        user_id=adjudicatario_user_id,
        metadata={
            "amount_refunded": amount_refunded,
            "fintech_operation_id": fintech_operation_id,
        },
    )



# ======================================================================
# 7) on_contract_close
# ======================================================================

def on_contract_close(session_id: str, operator_user_id: Optional[str]) -> None:

    contract = get_contract_by_session_id(session_id)
    if contract is None:
        return

    if contract.status not in (
        ContractStatus.DELIVERED,
        ContractStatus.PROVIDER_PAID,
        ContractStatus.REFUNDED,
    ):
        return

    mark_closed(contract)

    audit.log(
        action="CONTRACT_CLOSED",
        session_id=session_id,
        user_id=operator_user_id,
    )
