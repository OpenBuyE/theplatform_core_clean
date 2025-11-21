# tests/test_fintech_routes.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from server import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_orchestrator():
    with patch("backend_core.api.fintech_routes.wallet_orchestrator") as mock:
        yield mock


# ---------------------------------------------------------
# 1) Deposit OK
# ---------------------------------------------------------

def test_fintech_deposit_ok(client, mock_orchestrator):
    payload = {
        "session_id": "S1",
        "participant_id": "U1",
        "amount": 30.0,
        "currency": "EUR",
        "fintech_tx_id": "tx123",
        "status": "AUTHORIZED",
    }

    response = client.post(
        "/fintech/deposit-ok",
        json=payload,
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    mock_orchestrator.handle_deposit_ok.assert_called_once()


# ---------------------------------------------------------
# 2) Settlement
# ---------------------------------------------------------

def test_fintech_settlement(client, mock_orchestrator):
    payload = {
        "session_id": "S1",
        "adjudicatario_id": "U9",
        "fintech_batch_id": "batch001",
        "status": "SETTLED",
    }

    response = client.post(
        "/fintech/settlement",
        json=payload,
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    mock_orchestrator.handle_settlement.assert_called_once()


# ---------------------------------------------------------
# 3) Force majeure refund
# ---------------------------------------------------------

def test_fintech_force_majeure_refund(client, mock_orchestrator):
    payload = {
        "session_id": "S1",
        "adjudicatario_id": "U9",
        "product_amount": 300.0,
        "currency": "EUR",
        "reason": "Stock irreversible",
    }

    response = client.post(
        "/fintech/force-majeure-refund",
        json=payload,
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    mock_orchestrator.handle_force_majeure_refund.assert_called_once()
