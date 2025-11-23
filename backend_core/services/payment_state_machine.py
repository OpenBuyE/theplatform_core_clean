# backend_core/services/payment_state_machine.py
from __future__ import annotations

from datetime import datetime
from typing import Tuple

from backend_core.models.payment_state import (
    PaymentEvent,
    PaymentStateSnapshot,
    PaymentStatus,
)


class IllegalPaymentTransitionError(Exception):
    """
    Se lanza cuando se intenta aplicar un evento no permitido
    desde el estado actual. Importante para mantener el sistema
    determinista y auditable.
    """


class PaymentStateMachine:
    """
    Máquina de estados FINITA y DETERMINISTA.
    No realiza I/O.
    Solo recibe un snapshot + event y devuelve un nuevo snapshot.
    """

    @staticmethod
    def transition(
        snapshot: PaymentStateSnapshot,
        event: PaymentEvent,
    ) -> PaymentStateSnapshot:
        """
        Aplica un evento y devuelve un NUEVO snapshot (no muta el original).
        """
        current = snapshot.status

        # Mapa de transiciones permitido
        next_state, update_fn = PaymentStateMachine._decide_next_state(
            current, event
        )

        # Aplica la función de actualización específica (p.ej. sumar depósitos)
        new_data = snapshot.model_copy(deep=True)
        new_data.status = next_state
        new_data.updated_at = datetime.utcnow()

        update_fn(new_data)

        return new_data

    @staticmethod
    def _decide_next_state(
        status: PaymentStatus,
        event: PaymentEvent,
    ) -> Tuple[PaymentStatus, callable]:
        """
        Devuelve (next_status, update_fn) o lanza IllegalPaymentTransitionError.
        """

        def _noop(snapshot: PaymentStateSnapshot) -> None:
            return

        def _mark_force_majeure(snapshot: PaymentStateSnapshot) -> None:
            snapshot.force_majeure = True

        # ----- TRANSICIONES -----
        # Esquema general:
        # WAITING_DEPOSITS
        #   ├─ PARTICIPANT_DEPOSIT_AUTHORIZED → WAITING_DEPOSITS (no cambia agregate)
        #   ├─ ALL_DEPOSITS_OK → DEPOSITS_OK
        #   └─ FORCE_MAJEURE_TRIGGERED → FORCE_MAJEURE
        #
        # DEPOSITS_OK
        #   ├─ ADJUDICATION_COMPLETED → WAITING_SETTLEMENT
        #   └─ FORCE_MAJEURE_TRIGGERED → FORCE_MAJEURE
        #
        # WAITING_SETTLEMENT
        #   ├─ SETTLEMENT_CONFIRMED → SETTLED
        #   └─ FORCE_MAJEURE_TRIGGERED → FORCE_MAJEURE
        #
        # SETTLED
        #   └─ (solo FORCE_MAJEURE_TRIGGERED en escenarios muy extremos → FORCE_MAJEURE)
        #
        # FORCE_MAJEURE
        #   └─ FORCE_MAJEURE_REFUNDED → FORCE_MAJEURE (estado final estable)

        if status == PaymentStatus.WAITING_DEPOSITS:
            if event == PaymentEvent.PARTICIPANT_DEPOSIT_AUTHORIZED:
                return PaymentStatus.WAITING_DEPOSITS, _noop
            if event == PaymentEvent.ALL_DEPOSITS_OK:
                return PaymentStatus.DEPOSITS_OK, _noop
            if event == PaymentEvent.FORCE_MAJEURE_TRIGGERED:
                return PaymentStatus.FORCE_MAJEURE, _mark_force_majeure

        elif status == PaymentStatus.DEPOSITS_OK:
            if event == PaymentEvent.ADJUDICATION_COMPLETED:
                return PaymentStatus.WAITING_SETTLEMENT, _noop
            if event == PaymentEvent.FORCE_MAJEURE_TRIGGERED:
                return PaymentStatus.FORCE_MAJEURE, _mark_force_majeure

        elif status == PaymentStatus.WAITING_SETTLEMENT:
            if event == PaymentEvent.SETTLEMENT_CONFIRMED:
                return PaymentStatus.SETTLED, _noop
            if event == PaymentEvent.FORCE_MAJEURE_TRIGGERED:
                return PaymentStatus.FORCE_MAJEURE, _mark_force_majeure

        elif status == PaymentStatus.SETTLED:
            if event == PaymentEvent.FORCE_MAJEURE_TRIGGERED:
                # Caso muy excepcional: retroceso por orden judicial, etc.
                return PaymentStatus.FORCE_MAJEURE, _mark_force_majeure

        elif status == PaymentStatus.FORCE_MAJEURE:
            if event == PaymentEvent.FORCE_MAJEURE_REFUNDED:
                # Seguimos en FORCE_MAJEURE pero dejamos trazado el reembolso.
                return PaymentStatus.FORCE_MAJEURE, _noop

        raise IllegalPaymentTransitionError(
            f"Evento {event} no permitido desde estado {status}"
        )
