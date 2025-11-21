"""
wallet_orchestrator.py
----------------------
Orquestador que coordina la lógica entre:
- Smart Contract (contract_engine)
- Sistema de sesiones
- Fintech (MangoPay u otra)
- Repositorios internos

Este módulo contiene la lógica "core" del movimiento de dinero,
pero NO habla directamente con MangoPay.
Para eso existe mangopay_client.py.
"""

from .mangopay_adapter import mangopay
from .contract_engine import contract_engine
from .session_repository import session_repository
from .audit_repository import log_event


class WalletOrchestrator:

    # ======================================================
    # 1) Depósito OK por parte de un participante
    # ======================================================
    def handle_deposit_ok(self, session_id: str, participant_id: str,
                          amount: float, currency: str,
                          fintech_tx_id: str, status: str):

        # Notificar al smart contract
        contract_engine.on_deposit_ok(
            session_id=session_id,
            participant_id=participant_id,
            amount=amount
        )

        log_event(
            action="wallet_orchestrator_deposit_ok",
            session_id=session_id,
            user_id=participant_id,
            metadata={
                "fintech_tx_id": fintech_tx_id,
                "amount": amount,
                "currency": currency,
                "status": status
            }
        )

    # ======================================================
    # 2) Liquidación completada por la Fintech
    # ======================================================
    def handle_settlement_completed(self, session_id: str, adjudicatario_id: str,
                                    fintech_batch_id: str, status: str):

        contract_engine.on_settlement_completed(
            session_id=session_id,
            adjudicatario_id=adjudicatario_id
        )

        log_event(
            action="wallet_orchestrator_settlement_completed",
            session_id=session_id,
            user_id=adjudicatario_id,
            metadata={
                "fintech_batch_id": fintech_batch_id,
                "status": status
            }
        )

    # ======================================================
    # 3) Caso excepcional: fuerza mayor
    # ======================================================
    def handle_force_majeure_refund(self, session_id: str, adjudicatario_id: str,
                                    product_amount: float, currency: str,
                                    fintech_refund_tx_id: str | None, reason: str | None):

        # Notificar al smart contract
        contract_engine.on_force_majeure_refund(
            session_id=session_id,
            adjudicatario_id=adjudicatario_id,
            product_amount=product_amount
        )

        log_event(
            action="wallet_orchestrator_force_majeure_refund",
            session_id=session_id,
            user_id=adjudicatario_id,
            metadata={
                "product_amount": product_amount,
                "currency": currency,
                "fintech_refund_tx_id": fintech_refund_tx_id,
                "reason": reason
            }
        )


wallet_orchestrator = WalletOrchestrator()
