# backend_core/api/internal_routes.py

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Optional

# ======================================
# Repositories & Services
# ======================================

# Session / Participants
from backend_core.services.session_repository import (
    get_session_by_id,
)
from backend_core.services.participant_repository import (
    create_test_participant,
)
from backend_core.services.adjudicator_engine import adjudicator_engine
from backend_core.services.session_engine import session_engine

# Contract
from backend_core.services.contract_engine import (
    on_settlement_requested,
    on_delivery_confirmed,
    on_contract_close,
)

# MangoPay / Operators
from backend_core.services.operator_repository import (
    get_operator_by_id,
    update_operator_mangopay_ids,
    update_operator_kyc_status,
    log_operator_kyc_event,
)
from backend_core.services.mangopay_client import (
    create_legal_user,
    create_wallet_for_operator,
    create_kyc_document,
    upload_kyc_document_page,
    submit_kyc_document,
    get_kyc_document,
    get_legal_user,
)
from backend_core.models.operator import OperatorKycStatus


router = APIRouter()


# ============================================================
# INTERNAL DEBUG — FOR TESTING PURPOSES ONLY
# ============================================================

@router.post("/internal/debug/add-test-participant")
def debug_add_test_participant(session_id: str):
    """
    Añade un participante ficticio a una sesión activa (solo debug).
    """
    session = get_session_by_id(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    p = create_test_participant(session_id)
    return {"ok": True, "participant": p}


@router.post("/internal/debug/force-award")
def debug_force_award(session_id: str):
    """
    Fuerza adjudicación (solo debug).
    """
    result = adjudicator_engine.force_award(session_id)
    return {"ok": True, "result": result}


# ============================================================
# INTERNAL CONTRACT API
# ============================================================

@router.get("/internal/contract/{session_id}")
def get_contract_inspection(session_id: str):
    """
    Vista interna del estado contractual + pagos para una sesión.
    """
    result = adjudicator_engine.inspect_contract_state(session_id)
    if not result:
        raise HTTPException(404, "Contract or session not found")
    return {"ok": True, "data": result}


@router.post("/internal/contract/{session_id}/request-settlement")
def contract_request_settlement(session_id: str, operator_user_id: Optional[str] = None):
    """
    Solicita settlement al contract engine.
    """
    on_settlement_requested(session_id, operator_user_id)
    return {"ok": True, "session_id": session_id}


@router.post("/internal/contract/{session_id}/confirm-delivery")
def contract_confirm_delivery(
    session_id: str,
    adjudicatario_user_id: str,
    delivery_method: Optional[str] = None,
    delivery_location: Optional[str] = None,
    delivery_metadata: Optional[dict] = None,
):
    """
    Confirma la entrega del producto por parte del adjudicatario.
    """
    on_delivery_confirmed(
        session_id=session_id,
        adjudicatario_user_id=adjudicatario_user_id,
        delivery_method=delivery_method,
        delivery_location=delivery_location,
        delivery_metadata=delivery_metadata,
    )
    return {"ok": True, "session_id": session_id}


@router.post("/internal/contract/{session_id}/close-contract")
def contract_close(session_id: str, operator_user_id: Optional[str] = None):
    """
    Cierra un contrato ya entregado / pagado / reembolsado.
    """
    on_contract_close(session_id, operator_user_id)
    return {"ok": True, "session_id": session_id}


# ============================================================
# INTERNAL OPERATOR ONBOARDING (MangoPay KYC/KYB)
# ============================================================

@router.post("/internal/operators/{operator_id}/create-mangopay-account")
def create_mangopay_account(operator_id: str):
    """
    Crea el usuario legal + wallet del operador en MangoPay.
    """
    operator = get_operator_by_id(operator_id)
    if not operator:
        raise HTTPException(404, "Operator not found")

    # Valores de ejemplo; en producción, vendrán del panel
    legal_user = create_legal_user(
        name=operator.name,
        legal_person_type=operator.legal_person_type or "BUSINESS",
        email="operator@example.com",
        headquarters_address={
            "AddressLine1": "Calle Falsa 123",
            "City": "Madrid",
            "Country": "ES",
            "PostalCode": "28001"
        },
        legal_representative={
            "first_name": "John",
            "last_name": "Doe",
            "email": "legal@example.com",
            "birthday": 631152000,  # 1990-01-01
            "nationality": "ES",
            "residence": "ES"
        },
        country=operator.country or "ES",
    )

    wallet = create_wallet_for_operator(legal_user["Id"])

    update_operator_mangopay_ids(
        operator_id,
        mangopay_legal_user_id=legal_user["Id"],
        mangopay_wallet_id=wallet["Id"],
    )

    log_operator_kyc_event(
        operator_id,
        "MANGOPAY_ACCOUNT_CREATED",
        mangopay_kyc_id=None,
        status="created",
        payload={"legal_user": legal_user, "wallet": wallet},
    )

    return {
        "ok": True,
        "legal_user": legal_user,
        "wallet": wallet,
    }


@router.post("/internal/operators/{operator_id}/upload-kyc-document")
def upload_kyc_document_api(operator_id: str, doc_type: str = "IDENTITY_PROOF"):
    """
    Crea + sube documento KYC a MangoPay para un operador.
    En producción, el panel enviará el archivo real.
    """
    operator = get_operator_by_id(operator_id)
    if not operator:
        raise HTTPException(404, "Operator not found")

    if not operator.mangopay_legal_user_id:
        raise HTTPException(400, "Operator has no MangoPay legal user")

    doc = create_kyc_document(operator.mangopay_legal_user_id, doc_type)

    # Subimos un archivo ficticio (panel enviará uno real posteriormente)
    upload_kyc_document_page(
        operator.mangopay_legal_user_id,
        doc["Id"],
        b"fake-content",
    )

    submit_kyc_document(operator.mangopay_legal_user_id, doc["Id"])

    log_operator_kyc_event(
        operator_id,
        "KYC_DOCUMENT_SUBMITTED",
        mangopay_kyc_id=doc["Id"],
        status="submitted",
        payload=doc,
    )

    return {"ok": True, "document": doc}


@router.get("/internal/operators/{operator_id}/sync-kyc-status")
def sync_kyc_status(operator_id: str):
    """
    Consulta MangoPay y sincroniza estado KYC del operador.
    """
    operator = get_operator_by_id(operator_id)
    if not operator:
        raise HTTPException(404, "Operator not found")

    if not operator.mangopay_legal_user_id:
        raise HTTPException(400, "Operator has no MangoPay legal user")

    user_data = get_legal_user(operator.mangopay_legal_user_id)

    kyc_level = user_data.get("KYCLevel")

    if kyc_level == "REGULAR":
        new_status = OperatorKycStatus.VALIDATED
    elif kyc_level == "LIGHT":
        new_status = OperatorKycStatus.IN_REVIEW
    else:
        new_status = OperatorKycStatus.PENDING

    update_operator_kyc_status(operator_id, new_status, kyc_level)

    log_operator_kyc_event(
        operator_id,
        "KYC_STATUS_SYNC",
        mangopay_kyc_id=None,
        status=new_status.value,
        payload=user_data,
    )

    return {
        "ok": True,
        "new_status": new_status.value,
        "kyc_level": kyc_level,
        "raw": user_data,
    }
