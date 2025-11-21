"""
wallet_events.py
Capa de eventos estructurados del Wallet para Compra Abierta.

Responsabilidad:
- Registrar de forma consistente todos los eventos relacionados con la Fintech.
- NO contiene lógica de negocio.
- NO modifica sesiones ni participantes.
- Todos los eventos van al audit_log para trazabilidad completa.

Eventos incluidos:
1) Depósito autorizado
2) Liquidación ejecutada
3) Reembolso por fuerza mayor
"""

from backend_core.services.audit_repository import log_event


# -----------------------------------------------------
# 1) DEPÓSITO AUTORIZADO
# -----------------------------------------------------
def emit_deposit_authorized(
    session_id: str,
    participant_id: str,
    amount: float,
    currency: str,
    fintech_tx_id: str,
    status: str,
) -> None:
    """
    Evento emitido cuando la Fintech autoriza y bloquea un depósito.
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


# -----------------------------------------------------
# 2) LIQUIDACIÓN EJECUTADA (Proveedor + OÜ + DMHG)
# -----------------------------------------------------
def emit_settlement_executed(
    session_id: str,
    adjudicatario_id: str,
    fintech_batch_id: str,
    status: str,
) -> None:
    """
    Evento emitido cuando la Fintech liquida:
    - Pago a proveedor
    - Comisión para la OÜ
    - Gastos de gestión para DMHG (España)
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


# -----------------------------------------------------
# 3) REEMBOLSO POR FUERZA MAYOR
# -----------------------------------------------------
def emit_force_majeure_refund(
    session_id: str,
    adjudicatario_id: str,
    product_amount: float,
    currency: str,
    fintech_refund_tx_id: str | None,
    reason: str | None,
) -> None:
    """
    Evento emitido cuando el proveedor NO puede entregar el producto.
    - Solo se devuelve el precio del producto al adjudicatario.
    - NO se devuelve comisión ni gastos de gestión.
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
