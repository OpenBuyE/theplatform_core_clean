"""
wallet_events.py
Capa mínima de emisión de eventos de wallet / fintech.

Objetivo:
- Registrar eventos estructurados en audit_logs.
- Mantener trazabilidad clara entre:
  - Depósitos autorizados
  - Liquidaciones ejecutadas
  - Reembolsos por fuerza mayor

Este módulo NO ejecuta lógica contractual.
Solamente registra eventos.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from .audit_repository import log_event


# ---------------------------------------------------------
# 1) Depósito autorizado / bloqueado en la Fintech
# ---------------------------------------------------------
def emit_deposit_authorized(
    session_id: str,
    participant_id: str,
    amount: float,
    currency: str,
    fintech_tx_id: str,
    status: str,
) -> None:
    """
    Emite el evento cuando un depósito ha sido autorizado por la Fintech.
    """

    log_event(
        action="wallet_deposit_authorized",
        session_id=session_id,
        user_id=participant_id,
        metadata={
            "amount": amount,
            "currency": currency,
            "fintech_tx_id": fintech_tx_id,
            "status": status,
            "event_at": datetime.utcnow().isoformat(),
        }
    )


# ---------------------------------------------------------
# 2) Liquidación ejecutada por la Fintech
# ---------------------------------------------------------
def emit_settlement_executed(
    session_id: str,
    adjudicatario_id: str,
    fintech_batch_id: str,
    status: str,
) -> None:
    """
    Emite el evento cuando la Fintech ejecuta el pago al proveedor
    y se distribuyen comisiones/gastos según proceda.
    """

    log_event(
        action="wallet_settlement_executed",
        session_id=session_id,
        user_id=adjudicatario_id,
        metadata={
            "fintech_batch_id": fintech_batch_id,
            "status": status,
            "event_at": datetime.utcnow().isoformat(),
        }
    )


# ---------------------------------------------------------
# 3) Devolución por fuerza mayor (solo precio del producto)
# ---------------------------------------------------------
def emit_force_majeure_refund(
    session_id: str,
    adjudicatario_id: str,
    product_amount: float,
    currency: str,
    fintech_refund_tx_id: Optional[str],
    reason: Optional[str],
) -> None:
    """
    Evento para reflejar la devolución extraordinaria al adjudicatario
    cuando el proveedor NO puede entregar el producto por fuerza mayor.
    """

    log_event(
        action="wallet_force_majeure_refund",
        session_id=session_id,
        user_id=adjudicatario_id,
        metadata={
            "product_amount": product_amount,
            "currency": currency,
            "fintech_refund_tx_id": fintech_refund_tx_id,
            "reason": reason,
            "event_at": datetime.utcnow().isoformat(),
        }
    )
