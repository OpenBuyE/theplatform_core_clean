# backend_core/services/payment_state_machine.py

from __future__ import annotations

from typing import Optional, Dict, Any

from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event

PAYMENT_SESSIONS_TABLE = "ca_payment_sessions"


# ============================================================
# FUNCIONES BÁSICAS SOBRE ca_payment_sessions
# ============================================================

def init_payment_session(session_id: str, awarded_participant_id: str) -> Dict[str, Any]:
    """
    Crea una fila en ca_payment_sessions para la sesión dada.
    Estado inicial: WAITING_DEPOSITS.
    """

    data = {
        "session_id": session_id,
        "status": "WAITING_DEPOSITS",
        "awarded_participant_id": awarded_participant_id,
        "total_deposited_amount": 0.0,
    }

    resp = table(PAYMENT_SESSIONS_TABLE).insert(data).execute()
    row = resp.data[0]

    log_event(
        "payment_session_init",
        session_id=session_id,
        metadata={
            "awarded_participant_id": awarded_participant_id,
            "status": "WAITING_DEPOSITS",
        },
    )

    return row


def get_payment_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Devuelve la fila de ca_payment_sessions asociada a session_id, si existe.
    """
    resp = (
        table(PAYMENT_SESSIONS_TABLE)
        .select("*")
        .eq("session_id", session_id)
        .single()
        .execute()
    )
    return resp.data


def update_payment_state(session_id: str, new_status: str) -> Dict[str, Any]:
    """
    Actualiza el campo status de la payment_session.
    new_status debe ser una de:
      - WAITING_DEPOSITS
      - DEPOSITS_OK
      - WAITING_SETTLEMENT
      - SETTLED
      - FORCE_MAJEURE
    """

    resp = (
        table(PAYMENT_SESSIONS_TABLE)
        .update({"status": new_status})
        .eq("session_id", session_id)
        .execute()
    )

    if not resp.data:
        raise RuntimeError(f"No se encontró payment_session para session_id {session_id}")

    row = resp.data[0]

    log_event(
        "payment_state_updated",
        session_id=session_id,
        metadata={"new_status": new_status},
    )

    return row


# ============================================================
# FUNCIONES CONVENIENCIA PARA WALLET_ORCHESTRATOR
# ============================================================

def mark_settlement(session_id: str) -> Dict[str, Any]:
    """
    Marca la sesión de pago como SETTLED.
    Usado por wallet_orchestrator.handle_settlement_executed.
    """
    return update_payment_state(session_id, "SETTLED")


def mark_force_majeure_refund(session_id: str) -> Dict[str, Any]:
    """
    Marca la sesión de pago como FORCE_MAJEURE.
    Usado por wallet_orchestrator.handle_force_majeure_refund.
    """
    return update_payment_state(session_id, "FORCE_MAJEURE")
