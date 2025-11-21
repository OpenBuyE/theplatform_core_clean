# tests/test_wallet_events.py

import pytest
from unittest.mock import patch

from backend_core.services.wallet_events import (
    emit_deposit_authorized,
    emit_settlement_executed,
    emit_force_majeure_refund,
)

# ---------------------------------------------------------
# Helper para mockear auditoría
# ---------------------------------------------------------

@pytest.fixture
def mock_log_event():
    with patch("backend_core.services.wallet_events.log_event") as mock:
        yield mock


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

def test_emit_deposit_authorized(mock_log_event):
    emit_deposit_authorized(
        session_id="S1",
        participant_id="U1",
        amount=30.0,
        currency="EUR",
        fintech_tx_id="tx123",
        status="AUTHORIZED",
    )

    mock_log_event.assert_called_once()
    call = mock_log_event.call_args.kwargs

    assert call["action"] == "wallet_deposit_authorized"
    assert call["session_id"] == "S1"
    assert call["user_id"] == "U1"
    assert call["metadata"]["amount"] == 30.0


def test_emit_settlement_executed(mock_log_event):
    emit_settlement_executed(
        session_id="S1",
        adjudicatario_id="U9",
        fintech_batch_id="batch77",
        status="SETTLED",
    )

    mock_log_event.assert_called_once()
    call = mock_log_event.call_args.kwargs

    assert call["action"] == "wallet_settlement_executed"
    assert call["metadata"]["fintech_batch_id"] == "batch77"


def test_emit_force_majeure_refund(mock_log_event):
    emit_force_majeure_refund(
        session_id="S1",
        adjudicatario_id="U9",
        product_amount=300.0,
        currency="EUR",
        fintech_refund_tx_id="rf123",
        reason="Stock irreversible",
    )

    mock_log_event.assert_called_once()
    call = mock_log_event.call_args.kwargs

    assert call["action"] == "wallet_force_majeure_refund"
    assert call["metadata"]["product_amount"] == 300.0
