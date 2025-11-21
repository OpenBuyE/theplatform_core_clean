"""
wallet_events.py
Capa de eventos estructurados para wallet / fintech.

Cada evento:
- Se registra en audit_logs (trazabilidad total).
- Estandariza el formato del dato financiero.
- Deja preparado el punto para ser consumido por
  motor contractual, panel, o futuros workers.

Los nombres de los eventos son explícitos y NO usan
terminología de juegos de azar.
"""

from typing import Optional
from .audit_repository import log_event


# ---------------------------------------------------------
# 1) Depósito autorizado por la Fintech
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
    Evento: la Fintech confirma que un depósito está bloqueado/autorizado.
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
    Evento: Fintech ha liquidado fondos hacia proveedor + OÜ + DMHG.
    """
    log_event(
        action="wallet_settlement_executed",
        session_id=session_id,
        user_id=adjudicatario_id,
        metadata={
            "fintech_batch_id": fintech_batch_id,
            "status": status,
        }
    )


# ---------------------------------------------------------
# 3) Fuerza mayor: devolución al adjudicatario del precio del producto
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
    Evento: la Fintech devuelve al adjudicatario el importe del producto
    por imposibilidad de entrega.
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
        }
    )
