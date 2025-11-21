"""
wallet_events.py
----------------
Módulo responsable de recibir eventos externos (Fintech, sistema de pagos)
y traducirlos a llamadas al Wallet Orchestrator.

Este módulo NO contiene lógica de negocio.
Simplemente actúa como puente → unifica los eventos que pueden venir
del mundo exterior y los entrega al wallet_orchestrator.
"""

from typing import Dict, Any

from .wallet_orchestrator import wallet_orchestrator
from .audit_repository import log_event


class WalletEvents:

    # ---------------------------------------------------------
    # Depósito autorizado por la Fintech
    # ---------------------------------------------------------
    def on_deposit_ok(self, session_id: str, participant_id: str, amount: float,
                      currency: str, fintech_tx_id: str, status: str):
        log_event(
            action="wallet_event_deposit_ok",
            session_id=session_id,
            user_id=participant_id,
            metadata={
                "amount": amount,
                "currency": currency,
                "fintech_tx_id": fintech_tx_id,
                "status": status
            }
        )

        wallet_orchestrator.handle_deposit_ok(
            session_id=session_id,
            participant_id=participant_id,
            amount=amount,
            currency=currency,
            fintech_tx_id=fintech_tx_id,
            status=status
        )

    # ---------------------------------------------------------
    # Liquidación completada (pago a proveedor + comisiones)
    # ---------------------------------------------------------
    def on_settlement_completed(self, session_id: str, adjudicatario_id: str,
                                fintech_batch_id: str, status: str):
        log_event(
            action="wallet_event_settlement_completed",
            session_id=session_id,
            user_id=adjudicatario_id,
            metadata={
                "fintech_batch_id": fintech_batch_id,
                "status": status,
            }
        )

        wallet_orchestrator.handle_settlement_completed(
            session_id=session_id,
            adjudicatario_id=adjudicatario_id,
            fintech_batch_id=fintech_batch_id,
            status=status
        )

    # ---------------------------------------------------------
    # Caso excepcional: fuerza mayor
    # ---------------------------------------------------------
    def on_force_majeure_refund(self, session_id: str, adjudicatario_id: str,
                                product_amount: float, currency: str,
                                fintech_refund_tx_id: str | None, reason: str | None):
        log_event(
            action="wallet_event_force_majeure_refund",
            session_id=session_id,
            user_id=adjudicatario_id,
            metadata={
                "product_amount": product_amount,
                "currency": currency,
                "fintech_refund_tx_id": fintech_refund_tx_id,
                "reason": reason
            }
        )

        wallet_orchestrator.handle_force_majeure_refund(
            session_id=session_id,
            adjudicatario_id=adjudicatario_id,
            product_amount=product_amount,
            currency=currency,
            fintech_refund_tx_id=fintech_refund_tx_id,
            reason=reason
        )


# instancia global
wallet_events = WalletEvents()
