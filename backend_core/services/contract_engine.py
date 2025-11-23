# backend_core/services/contract_engine.py (esqueleto relevante)

def on_session_awarded(session_id: str, adjudicatario_user_id: str) -> None:
    """
    Llamado por adjudicator_engine cuando hay adjudicatario.
    - Crea / actualiza payment_session → WAITING_DEPOSITS
    - Registra en ca_audit_logs
    """


def on_participant_funded(
    session_id: str,
    user_id: str,
    amount: float,
    fintech_operation_id: str,
) -> None:
    """
    Llamado por WalletOrchestrator.handle_deposit_ok.
    - Marca depósito individual como autorizado.
    - Cuando TODOS los depósitos requeridos estén ok → llama a WalletOrchestrator.mark_all_deposits_ok
    """


def on_settlement_completed(
    session_id: str,
    provider_id: str,
    amount: float,
    fintech_operation_id: str,
) -> None:
    """
    Llamado por WalletOrchestrator.handle_settlement_completed.
    - Marca contrato como cumplido.
    - Actualiza estados de entrega/confirmación.
    """


def on_force_majeure_refund(
    session_id: str,
    adjudicatario_user_id: str,
    amount_refunded: float,
    fintech_operation_id: str,
) -> None:
    """
    Llamado por WalletOrchestrator.handle_force_majeure_refund.
    - Registra la resolución por fuerza mayor.
    - Garantiza que solo se devuelve precio producto, nunca fees.
    """
