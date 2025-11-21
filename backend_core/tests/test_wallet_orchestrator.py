import pytest
from unittest.mock import patch
from backend_core.services.wallet_orchestrator import wallet_orchestrator


@patch("backend_core.services.wallet_events.emit_deposit_authorized")
def test_handle_deposit_ok(mock_emit):
    data = {
        "session_id": "s1",
        "participant_id": "u1",
        "amount": 30,
        "currency": "EUR",
        "fintech_tx_id": "tx123",
        "status": "AUTHORIZED"
    }

    wallet_orchestrator.handle_deposit_ok(data)

    mock_emit.assert_called_once()


@patch("backend_core.services.wallet_events.emit_settlement_executed")
def test_handle_settlement(mock_emit):
    data = {
        "session_id": "s1",
        "adjudicatario_id": "u9",
        "fintech_batch_id": "batch1",
        "status": "SETTLED"
    }

    wallet_orchestrator.handle_settlement(data)
    mock_emit.assert_called_once()


@patch("backend_core.services.wallet_events.emit_force_majeure_refund")
def test_handle_force_majeure_refund(mock_emit):
    data = {
        "session_id": "s2",
        "adjudicatario_id": "u77",
        "product_amount": 300,
        "currency": "EUR",
        "fintech_refund_tx_id": "rfX",
        "reason": "Stock irreversible"
    }

    wallet_orchestrator.handle_force_majeure_refund(data)
    mock_emit.assert_called_once()
