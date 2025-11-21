"""
wallet_events.py
Capa de eventos del wallet / fintech para Compra Abierta.

Objetivo:
- Centralizar todos los eventos relacionados con:
  * Depósitos de participantes
  * Liquidaciones (pago proveedor + OÜ + DMHG)
  * Casos de fuerza mayor / devoluciones excepcionales

- Registrar SIEMPRE en audit_logs, con un naming claro y estable.

Este módulo NO habla con MangoPay directamente.
Eso lo hace mangopay_adapter / wallet_orchestrator.
"""

from typing import Optional, Dict, Any

from .audit_repository import log_event


def _emit_wallet_event(
    action: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Helper interno para emitir eventos de wallet en audit_logs.
    """

    log_event(
        action=action,
        session_id=session_id,
        user_id=user_id,
        organization_id=organization_id,
        metadata=metadata or {},
    )


# ---------------------------------------------------------
# 1) Depósito autorizado en Fintech
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
    Evento: la Fintech confirma que un depósito ha sido AUTORIZADO/BLOQUEADO.
    No significa todavía que la sesión esté adjudicada ni liquidada.
    """

    _emit_wallet_event(
        action="wallet_deposit_authorized",
        session_id=session_id,
        user_id=participant_id,
        metadata={
            "amount": amount,
            "currency": currency,
            "fintech_tx_id": fintech_tx_id,
            "status": status,
        },
    )


# ---------------------------------------------------------
# 2) Liquidación completada (pago al proveedor + OÜ + DMHG)
# ---------------------------------------------------------

def emit_settlement_executed(
    session_id: str,
    adjudicatario_id: str,
    fintech_batch_id: str,
    status: str,
) -> None:
    """
    Evento: la Fintech nos informa que ha ejecutado la liquidación
    de la sesión ya adjudicada.

    Incluye:
    - Pago al proveedor del producto
    - Transferencia de comisiones / gestión a OÜ / DMHG
    """

    _emit_wallet_event(
        action="wallet_settlement_executed",
        session_id=session_id,
        user_id=adjudicatario_id,
        metadata={
            "fintech_batch_id": fintech_batch_id,
            "status": status,
        },
    )


# ---------------------------------------------------------
# 3) Fuerza mayor: devolución SOLO precio del producto
# ---------------------------------------------------------

def emit_force_majeure_refund(
    session_id: str,
    adjudicatario_id: str,
    product_amount: float,
    currency: str,
    fintech_refund_tx_id: Optional[str] = None,
    reason: Optional[str] = None,
) -> None:
    """
    Evento: CASO EXCEPCIONAL (fuerza mayor)
    - El proveedor NO puede entregar el producto.
    - La Fintech devuelve al adjudicatario SOLO el precio del producto.
    - NO se devuelven comisiones ni gastos de gestión.
    """

    _emit_wallet_event(
        action="wallet_force_majeure_refund",
        session_id=session_id,
        user_id=adjudicatario_id,
        metadata={
            "product_amount": product_amount,
            "currency": currency,
            "fintech_refund_tx_id": fintech_refund_tx_id,
            "reason": reason,
        },
    )
