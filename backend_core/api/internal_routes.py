# backend_core/api/internal_routes.py

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Body

from backend_core.services import supabase_client
from backend_core.services.contract_engine import (
    on_settlement_requested,
    on_delivery_confirmed,
    on_contract_close,
)
from backend_core.services.contract_session_repository import (
    get_contract_by_session_id,
)
from backend_core.models.api_contract import (
    ContractFullView,
    ContractViewResponse,
)

router = APIRouter(prefix="/internal", tags=["internal"])


# ================================================================
# EXISTENTES: get-contract, request-settlement, confirm-delivery
# ================================================================

@router.get("/contract/{session_id}", response_model=ContractViewResponse)
async def get_contract_view(session_id: str):
    session_resp = (
        supabase_client.table("ca_sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )
    if not session_resp.data:
        raise HTTPException(status_code=404, detail="Session not found")

    session_row = session_resp.data

    from backend_core.services.payment_session_repository import (
        get_payment_session_by_session_id,
    )
    payment_session = get_payment_session_by_session_id(session_id)

    contract = get_contract_by_session_id(session_id)

    view = ContractFullView(
        contract=contract,
        payment_session=payment_session,
        session=session_row,
    )

    return ContractViewResponse(data=view)


@router.post("/contract/{session_id}/request-settlement")
async def request_settlement(session_id: str, operator_user_id: str | None = None):
    contract = get_contract_by_session_id(session_id)
    if contract is None:
        raise HTTPException(404, "Contract not found")

    on_settlement_requested(session_id, operator_user_id)

    return {
        "status": "ok",
        "message": "Settlement request registered",
        "session_id": session_id,
        "operator_user_id": operator_user_id,
    }


@router.post("/contract/{session_id}/confirm-delivery")
async def confirm_delivery(
    session_id: str,
    adjudicatario_user_id: str = Body(..., embed=True),
    delivery_method: str | None = Body(None, embed=True),
    delivery_location: str | None = Body(None, embed=True),
    delivery_metadata: dict | None = Body(None, embed=True),
):
    contract = get_contract_by_session_id(session_id)
    if contract is None:
        raise HTTPException(404, "Contract not found")

    on_delivery_confirmed(
        session_id=session_id,
        adjudicatario_user_id=adjudicatario_user_id,
        delivery_method=delivery_method,
        delivery_location=delivery_location,
        delivery_metadata=delivery_metadata,
    )

    return {
        "status": "ok",
        "message": "Delivery confirmed",
        "session_id": session_id,
        "adjudicatario_user_id": adjudicatario_user_id,
        "delivery_method": delivery_method,
        "delivery_location": delivery_location,
        "delivery_metadata": delivery_metadata,
    }


# ================================================================
# ⭐ NUEVO ENDPOINT → cierre formal del expediente contractual
# ================================================================

@router.post("/contract/{session_id}/close-contract")
async def close_contract(
    session_id: str,
    operator_user_id: str | None = Body(None, embed=True),
):
    """
    Cierra el expediente contractual cuando:
    - el producto ha sido entregado (DELIVERED)
    - o ha sido reembolsado (REFUNDED)
    - o se ha completado el proceso sin entrega pendiente (PROVIDER_PAID)

    Acción final del ciclo contractual.
    """

    contract = get_contract_by_session_id(session_id)
    if contract is None:
        raise HTTPException(404, "Contract not found")

    # Paso al Contract Engine
    on_contract_close(session_id, operator_user_id)

    return {
        "status": "ok",
        "message": "Contract successfully closed",
        "session_id": session_id,
        "operator_user_id": operator_user_id,
    }
