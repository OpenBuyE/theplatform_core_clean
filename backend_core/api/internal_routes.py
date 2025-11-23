# backend_core/api/internal_routes.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend_core.services import supabase_client
from backend_core.services.contract_engine import (
    on_settlement_requested,
)
from backend_core.services.contract_session_repository import (
    get_contract_by_session_id,
)
from backend_core.models.api_contract import (
    ContractFullView,
    ContractViewResponse,
)

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/contract/{session_id}", response_model=ContractViewResponse)
async def get_contract_view(session_id: str):
    """
    Vista completa del contrato y pagos.
    """
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


# -------------------------------------------------------
# ⭐ NUEVO ENDPOINT → request settlement (manual o admin)
# -------------------------------------------------------

@router.post("/contract/{session_id}/request-settlement")
async def request_settlement(session_id: str, operator_user_id: str | None = None):
    """
    Endpoint interno para solicitar el settlement (pago al proveedor).
    Este endpoint es usado por:
    - Operadores (Admin)
    - Panel interno de administración
    - Automatizaciones internas si fuera necesario

    Acciones:
    - Cambia el estado contractual a WAITING_SETTLEMENT
    - Deja traza en ca_audit_logs
    """

    contract = get_contract_by_session_id(session_id)
    if contract is None:
        raise HTTPException(404, "Contract not found")

    # Lógica contractual → engine
    on_settlement_requested(session_id, operator_user_id)

    return {
        "status": "ok",
        "message": "Settlement request registered",
        "session_id": session_id,
        "operator_user_id": operator_user_id,
    }
