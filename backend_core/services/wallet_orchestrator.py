"""
wallet_orchestrator.py
Capa de orquestación entre:

- Fintech (MangoPay / pasarela)
- Motor contractual (contract_engine)
- Capa de eventos (wallet_events)

En esta primera versión:
- Recibe datos "ya validados" desde la API (fintech_routes).
- Emite eventos de wallet (auditables).
- Deja listo el punto para enganchar con contract_engine.

Más adelante:
- Validará consistencia de importes.
- Verificará que TODOS los depósitos del grupo están OK
  antes de permitir la adjudicación y la liquidación.
"""

from typing import Dict, Any

from . import wallet_events
# En el futuro podemos conectar con el motor contractual:
# from .contract_engine import contract_engine


class WalletOrchestrator:
    """
    Orquestador principal de eventos de wallet / fintech.
    """

    # -----------------------------------------------------
    # 1) Depósito autorizado / bloqueado en la Fintech
    # -----------------------------------------------------
    def handle_deposit_ok(self, data: Dict[str, Any]) -> None:
        """
        data esperado (viene de fintech_routes.DepositNotification.dict()):
        {
            "session_id": "...",
            "participant_id": "...",
            "amount": 30.0,
            "currency": "EUR",
            "fintech_tx_id": "...",
            "status": "AUTHORIZED"
        }
        """

        session_id = data["session_id"]
        participant_id = data["participant_id"]
        amount = float(data["amount"])
        currency = data.get("currency", "EUR")
        fintech_tx_id = data.get("fintech_tx_id", "")
        status = data.get("status", "")

        # Emitimos evento estructurado
        wallet_events.emit_deposit_authorized(
            session_id=session_id,
            participant_id=participant_id,
            amount=amount,
            currency=currency,
            fintech_tx_id=fintech_tx_id,
            status=status,
        )

        # FUTURO:
        # contract_engine.on_participant_funded(session_id, participant_id, amount, currency)

    # -----------------------------------------------------
    # 2) Liquidación ejecutada por la Fintech
    # -----------------------------------------------------
    def handle_settlement(self, data: Dict[str, Any]) -> None:
        """
        data esperado (SettlementNotification.dict()):
        {
            "session_id": "...",
            "adjudicatario_id": "...",
            "fintech_batch_id": "...",
            "status": "SETTLED"
        }
        """

        session_id = data["session_id"]
        adjudicatario_id = data["adjudicatario_id"]
        fintech_batch_id = data.get("fintech_batch_id", "")
        status = data.get("status", "")

        wallet_events.emit_settlement_executed(
            session_id=session_id,
            adjudicatario_id=adjudicatario_id,
            fintech_batch_id=fintech_batch_id,
            status=status,
        )

        # FUTURO:
        # contract_engine.on_settlement_completed(session_id, adjudicatario_id, fintech_batch_id)

    # -----------------------------------------------------
    # 3) Fuerza mayor: devolución del precio del producto
    # -----------------------------------------------------
    def handle_force_majeure_refund(self, data: Dict[str, Any]) -> None:
        """
        data esperado (ForceMajeureRefund.dict()):
        {
            "session_id": "...",
            "adjudicatario_id": "...",
            "product_amount": 300.0,
            "currency": "EUR",
            "fintech_refund_tx_id": "...." | null,
            "reason": "Stock irreversible" | null
        }
        """

        session_id = data["session_id"]
        adjudicatario_id = data["adjudicatario_id"]
        product_amount = float(data["product_amount"])
        currency = data.get("currency", "EUR")
        fintech_refund_tx_id = data.get("fintech_refund_tx_id")
        reason = data.get("reason")

        wallet_events.emit_force_majeure_refund(
            session_id=session_id,
            adjudicatario_id=adjudicatario_id,
            product_amount=product_amount,
            currency=currency,
            fintech_refund_tx_id=fintech_refund_tx_id,
            reason=reason,
        )

        # FUTURO:
        # contract_engine.on_force_majeure_refund(session_id, adjudicatario_id, product_amount, currency, reason)


# Instancia global para usar desde la API
wallet_orchestrator = WalletOrchestrator()
