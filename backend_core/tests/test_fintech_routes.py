import pytest
from fastapi.testclient import TestClient
from backend_core.api.fastapi_app import app

client = TestClient(app)


# Usamos API key dummy
HEADERS = {"X-API-Key": "TEST123"}


def test_fintech_deposit_ok():
    payload = {
        "session_id": "s1",
        "participant_id": "u1",
        "amount": 30,
        "currency": "EUR",
        "fintech_tx_id": "tx1",
        "status": "AUTHORIZED"
    }
    r = client.post("/fintech/deposit-ok", json=payload, headers=HEADERS)
    assert r.status_code == 200


def test_fintech_settlement():
    payload = {
        "session_id": "s2",
        "adjudicatario_id": "u22",
        "fintech_batch_id": "batch1",
        "status": "SETTLED"
    }
    r = client.post("/fintech/settlement", json=payload, headers=HEADERS)
    assert r.status_code == 200


def test_fintech_force_majeure_refund():
    payload = {
        "session_id": "s3",
        "adjudicatario_id": "u33",
        "product_amount": 300,
        "currency": "EUR",
        "fintech_refund_tx_id": "rf99",
        "reason": "Stock irreversible"
    }
    r = client.post("/fintech/force-majeure-refund", json=payload, headers=HEADERS)
    assert r.status_code == 200
