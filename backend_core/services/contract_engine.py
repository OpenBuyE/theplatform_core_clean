"""
contract_engine.py
Motor contractual para Compra Abierta.

RESPONSABILIDADES:
- Registrar el resultado contractual de una sesión adjudicada
- Informar al wallet/orchestrator de los pasos financieros
- Registrar fuerza mayor
- Mantener trazabilidad y consistencia interna

IMPORTANTE:
- Este archivo **NO importa adjudicator_engine**
  para evitar ciclos circulares.
- adjudicator_engine llamará a: contract_engine.on_session_awarded(...)
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from .audit_repository import log_event
from .session_repository import session_repository
from .participant_repository import participant_repository

# Enlazaremos wallet_orchestrator SOLO DENTRO DE LOS MÉTODOS
# Para evitar ciclos en tiempo de carga
# from .wallet_orchestrator import wallet_orchestrator


class ContractEngine:
    """
    Motor contractual del proyecto.
    Este componente registra eventos legales-operativos
    que forman parte del Smart Contract determinista.
    """

    # ------------------------------------------------------------------
    # 1) Registro de adjudicación contractual (llamado por adjudicator_engine)
    # ------------------------------------------------------------------
    def on_session_awarded(
        self,
        session: Dict,
        participants: List[Dict],
        awarded_participant: Dict,
    ) -> None:
        """
        Método invocado cuando una sesión queda adjudicada
        por el motor determinista.
        """

        session_id = session["id"]
        adjudicatario_id = awarded_participant["id"]
        user_id = awarded_participant["user_id"]
        now_iso = datetime.utcnow().isoformat()

        # 1. Registrar evento contractual
        log_event(
            action="contract_session_awarded",
            session_id=session_id,
            user_id=user_id,
            metadata={
                "adjudicatario_participant_id": adjudicatario_id,
                "participants_count": len(participants),
            }
        )

        # 2. Notificar al wallet_orchestrator (import diferido)
        try:
            from .wallet_orchestrator import wallet_orchestrator

            wallet_orchestrator.on_session_awarded(
                session=session,
                participants=participants,
                awarded_participant=awarded_participant,
            )
        except Exception as e:
            log_event(
                action="contract_engine_wallet_notify_error",
                session_id=session_id,
                metadata={"error": str(e)}
            )

    # ------------------------------------------------------------------
    # 2) Registro de liquidación económica completada por Fintech
    # ------------------------------------------------------------------
    def on_settlement_completed(
        self,
        session_id: str,
        adjudicatario_id: str,
        fintech_batch_id: str
    ) -> None:

        log_event(
            action="contract_settlement_completed",
            session_id=session_id,
            user_id=adjudicatario_id,
            metadata={"fintech_batch_id": fintech_batch_id}
        )

    # ------------------------------------------------------------------
    # 3) Caso excepcional de fuerza mayor
    # ------------------------------------------------------------------
    def on_force_majeure_refund(
        self,
        session_id: str,
        adjudicatario_id: str,
        product_amount: float,
        currency: str,
        reason: Optional[str] = None,
        fintech_refund_tx_id: Optional[str] = None
    ) -> None:

        log_event(
            action="contract_force_majeure",
            session_id=session_id,
            user_id=adjudicatario_id,
            metadata={
                "product_amount": product_amount,
                "currency": currency,
                "reason": reason,
                "fintech_refund_tx_id": fintech_refund_tx_id
            }
        )

    # ------------------------------------------------------------------
    # 4) Utilidad: verificación interna (opcional, se ampliará)
    # ------------------------------------------------------------------
    def verify_all_deposits_ok(self, session_id: str) -> bool:
        """
        Verifica si TODOS los participantes han sido notificados como 'deposit_ok'.
        En versiones futuras se consultará wallet state.
        """
        # INTEGRACIÓN REAL → cuando wallet tenga un storage
        log_event(
            action="contract_verify_all_deposits_pending",
            session_id=session_id
        )
        return True  # placeholder actual

    # ------------------------------------------------------------------
    # 5) Integración manual (opcional de testing)
    # ------------------------------------------------------------------
    def simulate_manual_trigger(self, session_id: str) -> None:
        """
        Invocado manualmente para test.
        """
        session = session_repository.get_session_by_id(session_id)
        if not session:
            return

        participants = participant_repository.get_participants_by_session(session_id)
        awarded = participant_repository.get_awarded_participant(session_id)

        self.on_session_awarded(
            session=session,
            participants=participants,
            awarded_participant=awarded
        )


# Instancia global
contract_engine = ContractEngine()
