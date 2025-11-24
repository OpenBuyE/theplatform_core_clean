# backend_core/api/internal_routes.py

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Any, Dict

from backend_core.services.contract_engine import contract_engine
from backend_core.services.module_repository import (
    list_modules,
    get_module,
    assign_module_to_session,
)
from backend_core.services.audit_repository import log_event

router = APIRouter(prefix="/internal", tags=["internal"])


# ============================================================
# 1) ESTADO CONTRACTUAL (USADO POR DASHBOARD / OPERATOR VIEW)
# ============================================================

@router.get("/contract/{session_id}")
def get_contract_status(session_id: str) -> Dict[str, Any]:
    """
    Devuelve el estado contractual completo de una sesión.
    Se adapta al formato que usan las vistas de Streamlit:
    {
      "data": {
        "session": {...},
        "contract": {...},        # aquí devolvemos el módulo como "contract"
        "payment_session": {...}
      }
    }
    """
    data = contract_engine.get_contract_status(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "data": {
            "session": data["session"],
            "contract": data["module"],           # compatibilidad con UI antigua
            "payment_session": data["payment"],
        }
    }


# (Opcional / stubs actuales: confirmar entrega, cierre de contrato)
@router.post("/contract/{session_id}/confirm-delivery")
def confirm_delivery(session_id: str) -> Dict[str, Any]:
    """
    Endpoint stub para confirmar entrega.
    De momento solo registra en auditoría.
    """
    log_event("contract_confirm_delivery", session_id=session_id, user_id=None, metadata={})
    return {"ok": True, "session_id": session_id, "action": "confirm_delivery"}


@router.post("/contract/{session_id}/close-contract")
def close_contract(session_id: str) -> Dict[str, Any]:
    """
    Endpoint stub para cierre contractual manual.
    De momento solo registra en auditoría.
    """
    log_event("contract_closed_manual", session_id=session_id, user_id=None, metadata={})
    return {"ok": True, "session_id": session_id, "action": "close_contract"}


# ============================================================
# 2) ENDPOINTS KYC OPERATORS (STUBS PARA PANEL)
# ============================================================

@router.post("/operators/{operator_id}/create-mangopay-account")
def create_mangopay_account(operator_id: str) -> Dict[str, Any]:
    """
    Stub actual: simula la creación de cuenta MangoPay.
    Registra en auditoría y devuelve payload de prueba.
    """
    log_event(
        "operator_create_mangopay_account",
        session_id=None,
        user_id=None,
        metadata={"operator_id": operator_id},
    )
    return {
        "operator_id": operator_id,
        "status": "created_stub",
        "message": "Cuenta MangoPay simulada (stub).",
    }


@router.post("/operators/{operator_id}/upload-kyc-document")
def upload_kyc_document(operator_id: str) -> Dict[str, Any]:
    """
    Stub actual: simula el envío de un documento KYC.
    """
    log_event(
        "operator_upload_kyc_document",
        session_id=None,
        user_id=None,
        metadata={"operator_id": operator_id},
    )
    return {
        "operator_id": operator_id,
        "status": "kyc_document_uploaded_stub",
        "message": "Documento KYC simulado (stub).",
    }


@router.get("/operators/{operator_id}/sync-kyc-status")
def sync_kyc_status(operator_id: str) -> Dict[str, Any]:
    """
    Stub actual: simula la sincronización del estado KYC.
    """
    log_event(
        "operator_sync_kyc_status",
        session_id=None,
        user_id=None,
        metadata={"operator_id": operator_id},
    )
    # Simulamos un estado 'VALIDATED' para pruebas
    return {
        "operator_id": operator_id,
        "kyc_status": "VALIDATED_STUB",
        "message": "Estado KYC simulado (stub).",
    }


# ============================================================
# 3) API REST DE MÓDULOS (SESSION MODULES)
# ============================================================

@router.get("/modules")
def get_all_modules() -> Dict[str, Any]:
    """
    Lista todos los módulos (activos o no).
    """
    modules = list_modules()
    return {"modules": modules}


@router.get("/modules/{module_code}")
def get_single_module(module_code: str) -> Dict[str, Any]:
    """
    Devuelve un módulo concreto por su module_code.
    """
    module = get_module(module_code)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    return {"module": module}


@router.patch("/sessions/{session_id}/module/{module_code}")
def change_session_module(session_id: str, module_code: str) -> Dict[str, Any]:
    """
    Cambia el módulo de una sesión existente.
    Usa module_repository.assign_module_to_session.
    """

    try:
        updated = assign_module_to_session(session_id, module_code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    log_event(
        "module_changed_via_api",
        session_id=session_id,
        user_id=None,
        metadata={"new_module": module_code},
    )

    return {
        "ok": True,
        "session": updated,
    }
