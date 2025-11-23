"""
payment_state.py
Modelo de dominio para la máquina de estados de pago (Payment State Machine).

Este modelo NO ejecuta lógica de pago.
Solo define:

- Estados posibles del ciclo de pagos.
- Transiciones permitidas.
- Validaciones de integridad.
- Representación clara y unificada para wallet_orchestrator,
  contract_engine y fintech_routes.

La lógica final se implementa en:
- services/wallet_orchestrator.py
- services/contract_engine.py
- routes/fintech_routes.py
"""

from enum import Enum


class PaymentState(str, Enum):
    """
    Estados formales del ciclo de pagos de una sesión.

    El flujo normal sería:

        UNFUNDED
            ↓ (depósitos autorizados)
        FUNDED_GROUP
            ↓ (adjudicación determinista)
        AWARDED
            ↓ (li
