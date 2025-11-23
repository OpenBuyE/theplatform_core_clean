"""
payment_state.py
Dominio: Estados del flujo de pago para Compra Abierta.

Esta máquina de estados NO ejecuta lógica de pagos directamente;
sirve como una representación formal para que:

- contract_engine.py
- wallet_orchestrator.py
- fintech_routes.py
- tests/

puedan razonar siempre sobre los mismos estados y transiciones.

Estados posibles del ciclo completo:

1. PENDING_DEPOSITS
   · Los participantes están pagando en la Fintech.
   · No se puede adjudicar aún.

2. DEPOSITS_AUTHORIZED
   · Todos los depósitos han sido autorizados/bloqueados por la Fintech.
   · La sesión puede adjudicarse.

3. ADJUDICATED
   · El motor determinista eligió adjudicatario.
   · Falta procesar pago al proveedor y reparto.

4. SETTLEMENT_IN_PROGRESS
   · La Fintech está ejecutando liquidación (proveedor + OÜ + DMHG).

5. SETTLED
   · Liquidación completada correctamente.

6. FORCE_MAJEURE_REFUND
   · Caso excepcional: devolución del precio del producto al adjudicatario.
"""

from enum import Enum


class PaymentState(str, Enum):
    """
    Máquina de estados del ciclo económico completo
    de una sesión de Compra Abierta.
    """

    # ---------------------------------------------------------
    # 1) Participantes pagando en la Fintech
    # ---------------------------------------------------------
    PENDING_DEPOSITS = "pending_deposits"

    # ---------------------------------------------------------
    # 2) Todos los depósitos aprobados/bloqueados
    # ---------------------------------------------------------
    DEPOSITS_AUTHORIZED = "deposits_authorized"

    # ---------------------------------------------------------
    # 3) Motor determinista adjudica
    # ---------------------------------------------------------
    ADJUDICATED = "adjudicated"

    # ---------------------------------------------------------
    # 4) Fintech procesando liquidación
    # ---------------------------------------------------------
    SETTLEMENT_IN_PROGRESS = "settlement_in_progress"

    # ---------------------------------------------------------
    # 5) Liquidación finalizada
    # ---------------------------------------------------------
    SETTLED = "settled"

    # ---------------------------------------------------------
    # 6) Caso de fuerza mayor (stock inexistente etc.)
    # ---------------------------------------------------------
    FORCE_MAJEURE_REFUND = "force_majeure_refund"


# ---------------------------------------------------------
# VALIDACIONES DE TRANSICIÓN
# ---------------------------------------------------------

# Mapa de transiciones válidas: origen → posibles destinos
VALID_TRANSITIONS = {
    PaymentState.PENDING_DEPOSITS: {
        PaymentState.DEPOSITS_AUTHORIZED,
        PaymentState.FORCE_MAJEURE_REFUND,
    },

    PaymentState.DEPOSITS_AUTHORIZED: {
        PaymentState.ADJUDICATED,
        PaymentState.FORCE_MAJEURE_REFUND,
    },

    PaymentState.ADJUDICATED: {
        PaymentState.SETTLEMENT_IN_PROGRESS,
        PaymentState.FORCE_MAJEURE_REFUND,
    },

    PaymentState.SETTLEMENT_IN_PROGRESS: {
        PaymentState.SETTLED,
        PaymentState.FORCE_MAJEURE_REFUND,
    },

    PaymentState.SETTLED: set(),  # Fin del flujo

    PaymentState.FORCE_MAJEURE_REFUND: set(),  # Fin de flujo alternativo
}


def is_valid_transition(current: PaymentState, new: PaymentState) -> bool:
    """
    Retorna True si la transición está permitida según la máquina de estados.
    """
    allowed = VALID_TRANSITIONS.get(current, set())
    return new in allowed
