"""
wallet_events.py
Orquestador de eventos provenientes de la Fintech.

Objetivo:
- Recibir eventos normalizados (deposit_ok, settlement_ok, force_majeure_refund)
  desde los endpoints fintech_routes.py.
- Delegar acciones al wallet_orchestrator, contract_engine, adjudicator_engine
  cuando corresponda.
- Mantener un único punto interno de entrada para la capa Wallet.

NOTA:
En esta versión aún NO ejecutamos lógica compleja de Mangopay,
solo estructuramos el flujo.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from backend_core.services.audit_repository import log_event
from backend_core.services.session_repository import session_repository
from backend_core.services.participant_repository import participant_repository
from backend_core.services.contract_engine import contract_engine
from backend_core.services.wallet_orchestrator import wallet_orchestrator


class WalletEvents:

    # ---------------------------------------------------------
    # Evento 1: Depósito confirmado por la Fintech
    # ---------------------------------------------------------
    def on_deposit_ok(
        self,
        session_id: str,
        participant_id: str,
        amount: float,
        currency: str,
        fintech_tx_id: str,
        status: str
    ) -> None:

        # Registrar auditoría interna
        log_event(
            action="event_on_deposit_ok",
            session_id=session_id,
            user_id=participant_id,
            metadata={
                "amount": amount,
                "currency": currency,
                "fintech_tx_id": fintech_tx_id,
                "status": status,
            }
        )

        # Informar al Wallet Orchestrator
        wallet_orchestrator.mark_deposit_confirmed(
            session_id=session_id,
            participant_id=participant_id,
            amount=amount
        )

        # Lógica opcional (más adelante):
        # contract_engine.try_update_funding_state(session_id)

    # ---------------------------------------------------------
    # Evento 2: Liquidación ejecutada por la Fintech
    # ---------------------------------------------------------
    def on_settlement_completed(
        self,
        session_id: str,
        adjudicatario_id: str,
        fintech_batch_id: str,
        status: str
    ) -> None:

        log_event(
            action="event_on_settlement_completed",
            session_id=session_id,
            user_id=adjudicatario_id,
            metadata={
                "fintech_batch_id": fintech_batch_id,
                "status": status,
            }
        )

        # Avisar al contrato operativo
        contract_engine.on_settlement_completed(
            session_id=session_id,
            adjudicatario_id=adjudicatario_id,
            fintech_batch_id=fintech_batch_id
        )

        wallet_orchestrator.mark_settlement_completed(
            session_id=session_id,
            adjudicatario_id=adjudicatario_id
        )

    # ---------------------------------------------------------
    # Evento 3: Caso excepcional de fuerza mayor
    # ---------------------------------------------------------
    def on_force_majeure_refund(
        self,
        session_id: str,
        adjudicatario_id: str,
        product_amount: float,
        currency: str,
        fintech_refund_tx_id: Optional[str],
        reason: Optional[str],
    ) -> None:

        log_event(
            action="event_force_majeure_refund",
            session_id=session_id,
            user_id=adjudicatario_id,
            metadata={
                "product_amount": product_amount,
                "currency": currency,
                "fintech_refund_tx_id": fintech_refund_tx_id,
                "reason": reason,
            }
        )

        # Actualizar estado contractual
        contract_engine.on_force_majeure_refund(
            session_id=session_id,
            adjudicatario_id=adjudicatario_id,
            refunded_amount=product_amount,
            reason=reason
        )

        # Registrar internamente
        wallet_orchestrator.mark_force_majeure_refund(
            session_id=session_id,
            adjudicatario_id=adjudicatario_id,
            refunded_amount=product_amount
        )


# Instancia global (estilo repositorio/servicio)
wallet_events = WalletEvents()
