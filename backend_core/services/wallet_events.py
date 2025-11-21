"""
wallet_events.py
Capa simple y estable para generar eventos de wallet.
Cada evento se registra en audit_logs mediante log_event().
Sirve de base estable para pruebas unitarias y para conectar la
Fintech → Wallet Orchestrator → Smart Contract Engine.
"""

from datetime import datetime
from typing import Optional
from .audit_repository import log_event


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


# ---------------------------------------------------------
# 1) Depósito autorizado en Fintech
# ---------------------------------------------------------
def emit_deposit_authorized(
    session_id: str,
    participant_id: str,
    amount: float,
    currency: str,
    fintech_tx_id: str,
    status: str
) -> None:
    log_event(
        action="wallet_deposit_authorized",
        session_id=session_id,
        user_id=participant_id,
        metadata={
            "amount": amount,
            "currency": currency,
            "fintech_tx_id": fintech_tx_id,
            "status": status,
            "timestamp": _now_iso(),
        }
    )


# ---------------------------------------------------------
# 2) Liquidación completada (pago al proveedor + comisiones)
# ---------------------------------------------------------
def emit_settlement_executed(
    session_id: str,
    adjudicatario_id: str,
    fintech_batch_id: str,
    status: str
) -> None:
    log_event(
        action="wallet_settlement_executed",
        session_id=session_id,
        user_id=adjudicatario_id,
        metadata={
            "fintech_batch_id": fintech_batch_id,
            "status": status,
            "timestamp": _now_iso(),
        }
    )


# ---------------------------------------------------------
# 3) Fuerza mayor: devolución del precio del producto
# ---------------------------------------------------------
def emit_force_majeure_refund(
    session_id: str,
    adjudicatario_id: str,
    product_amount: float,
    currency: str,
    fintech_refund_tx_id: Optional[str],
    reason: Optional[str]
) -> None:
    log_event(
        action="wallet_force_majeure_refund",
        session_id=session_id,
        user_id=adjudicatario_id,
        metadata={
            "product_amount": product_amount,
            "currency": currency,
            "fintech_refund_tx_id": fintech_refund_tx_id,
            "reason": reason,
            "timestamp": _now_iso(),
        }
    )
