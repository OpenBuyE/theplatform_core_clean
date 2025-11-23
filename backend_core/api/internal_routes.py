# backend_core/api/internal_routes.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend_core.services import supabase_client
from backend_core.services.contract_session_repository import (
    get_contract_by_session_id,
)
from backend_core.services.payment_session_repository import (
    get_payment_session_by_session_id,
)
from backend_core.models.api_contract import (
    ContractFullView,
    ContractViewResponse,
)

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/contract/{session_id}", response_model=ContractViewResponse)
async def get_contract_view(session_id: str):
    """
    Devuelve la vista completa del contrato de una sesión:
    - ContractSession
    - PaymentSession
    - Datos básicos de la sesión
    """

    # 1) Cargar session
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

    # 2) Cargar contract_session
    contract = get_contract_by_session_id(session_id)

    # 3) Cargar payment_session
    payment_session = get_payment_session_by_session_id(session_id)

    # 4) Construir la respuesta
    view = ContractFullView(
        contract=contract,
        payment_session=payment_session,
        session=session_row,
    )

    return ContractViewResponse(data=view)
