import pytest
from unittest.mock import patch
from backend_core.services import wallet_events


@patch("backend_core.services.wallet_events.log_event")
def test_emit_deposit_authorized(mock_log):
    wallet_events.emit_deposit_authorized(
        session_id="s1",
        participant_id="u1",
        amount=30,
        currency="EUR",
        fintech_tx_id="tx123",
        status="AUTHORIZED",
    )

    mock_log.assert_called_once()
    args, kwargs = mock_log.call_args
    assert kwargs["action"] == "wallet_deposit_authorized"
    assert kwargs["session_id"] == "s1"
    assert kwargs["user_id"] == "u1"
    assert kwargs["metadata"]["amount"] == 30


@patch("backend_core.services.wallet_events.log_event")
def test_emit_settlement_executed(mock_log):
    wallet_events.emit_settlement_executed(
        session_id="s2",
        adjudicatario_id="u9",
        fintech_batch_id="batch001",
        status="SETTLED",
    )

    mock_log.assert_called_once()
    args, kwargs = mock_log.call_args
    assert kwargs["action"] == "wallet_settlement_executed"
    assert kwargs["metadata"]["fintech_batch_id"] == "batch001"


@patch("backend_core.services.wallet_events.log_event")
def test_emit_force_majeure_refund(mock_log):
    wallet_events.emit_force_majeure_refund(
        session_id="s3",
        adjudicatario_id="u5",
        product_amount=300,
        currency="EUR",
        fintech_refund_tx_id="rf001",
        reason="Stock"
    )

    mock_log.assert_called_once()
    args, kwargs = mock_log.call_args
    assert kwargs["action"] == "wallet_force_majeure_refund"
    assert kwargs["metadata"]["product_amount"] == 300
