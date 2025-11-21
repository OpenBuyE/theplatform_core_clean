# tests/test_wallet_orchestrator.py

import pytest
from unittest.mock import patch

from backend_core.services.wallet_orchestrator import wallet_orchestrator


@pytest.fixture
def mock_events():
    with patch("backend_core.services.wallet_orchestrator.wallet_events") as mock:
        yield mock


# ---------------------------------------------------------
# 1) Depósito autorizado
# ---------------------------------------------------------

def test_handle_deposit_ok(mock_events):
    payload = {
        "session_id": "S1",
        "participant_id": "U1",
        "amount": 30.0,
        "currency": "EUR",
        "fintech_tx_id": "tx999",
        "status": "AUTHORIZED",
    }

    wallet_orchestrator.handle_deposit_ok(payload)

    mock_events.emit_deposit_authorized.assert_called_once()
    call = mock_events.emit_deposit_authorized.call_args.kwargs

    assert call["session_id"] == "S1"
    assert call["amount"] == 30.0


# ---------------------------------------------------------
# 2) Liquidación
# ---------------------------------------------------------

def test_handle_settlement(mock_events):
    payload = {
        "session_id": "S1",
        "adjudicatario_id": "U9",
        "fintech_batch_id": "batch77",
        "status": "SETTLED",
    }

    wallet_orchestrator.handle_settlement(payload)

    mock_events.emit_settlement_executed.assert_called_once()
    call = mock_events.emit_settlement_executed.call_args.kwargs

    assert call["fintech_batch_id"] == "batch77"


# ---------------------------------------------------------
# 3) Fuerza mayor
# ---------------------------------------------------------

def test_handle_force_majeure(mock_events):
    payload = {
        "session_id": "S1",
        "adjudicatario_id": "U9",
        "product_amount": 300.0,
        "currency": "EUR",
        "fintech_refund_tx_id": "rf123",
        "reason": "Stock irreversible",
    }

    wallet_orchestrator.handle_force_majeure_refund(payload)

    mock_events.emit_force_majeure_refund.assert_called_once()
    call = mock_events.emit_force_majeure_refund.call_args.kwargs

    assert call["product_amount"] == 300.0
    assert call["reason"] == "Stock irreversible"
