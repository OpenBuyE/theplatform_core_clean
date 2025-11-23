# backend_core/tests/test_payment_flow_e2e.py
from __future__ import annotations

from datetime import datetime

import pytest

from backend_core.models.payment_state import (
    PaymentStateSnapshot,
    PaymentStatus,
)
from backend_core.services.audit_repository import AuditRepository
from backend_core.services.wallet_events import (
    DepositOkEvent,
    SettlementCompletedEvent,
)
from backend_core.services.wallet_orchestrator import WalletOrchestrator
from backend_core.services import contract_engine, supabase_client


class InMemoryAuditRepository(AuditRepository):
    def __init__(self):
        self.events = []

    def log(self, action, session_id, user_id, metadata=None):
        self.events.append(
            {
                "action": action,
                "session_id": session_id,
                "user_id": user_id,
                "metadata": metadata or {},
            }
        )


@pytest.fixture
def in_memory_payment_state(monkeypatch):
    """
    Simula ca_payment_sessions en memoria.
    """
    state = {
        "id": "pay_1",
        "session_id": "sess_1",
        "status": PaymentStatus.WAITING_DEPOSITS.value,
        "total_expected_amount": 100.0,
        "total_deposited_amount": 0.0,
        "total_settled_amount": 0.0,
        "force_majeure": False,
        "updated_at": datetime.utcnow().isoformat(),
        "metadata": {},
    }

    class DummyTable:
        def __init__(self, name):
            self.name = name

        def select(self, *args, **kwargs):
            return self

        def eq(self, *args, **kwargs):
            return self

        def single(self):
            return self

        def execute(self):
            class Resp:
                data = state
            return Resp()

        def update(self, payload):
            # Actualizamos el dict in-memory
            state.update(payload)
            return self

    class DummyClient:
        def table(self, name):
            return DummyTable(name)

    monkeypatch.setattr(
        "backend_core.services.supabase_client", DummyClient()
    )

    return state


@pytest.fixture
def dummy_contract_engine(monkeypatch):
    """
    Stub de contract_engine para no hacer I/O ni lógica real.
    Guarda las llamadas para poder asertar.
    """
    calls = {
        "on_participant_funded": [],
        "on_settlement_completed": [],
    }

    def on_participant_funded(session_id, user_id, amount, fintech_operation_id):
        calls["on_participant_funded"].append(
            {
                "session_id": session_id,
                "user_id": user_id,
                "amount": amount,
                "op_id": fintech_operation_id,
            }
        )

    def on_settlement_completed(session_id, provider_id, amount, fintech_operation_id):
        calls["on_settlement_completed"].append(
            {
                "session_id": session_id,
                "provider_id": provider_id,
                "amount": amount,
                "op_id": fintech_operation_id,
            }
        )

    monkeypatch.setattr(
        contract_engine, "on_participant_funded", on_participant_funded
    )
    monkeypatch.setattr(
        contract_engine, "on_settlement_completed", on_settlement_completed
    )

    return calls


def test_full_payment_flow(
    in_memory_payment_state, dummy_contract_engine
):
    """
    Escenario simplificado:
    - Estado inicial: WAITING_DEPOSITS
    - Llega un DEPOSIT_OK
    - Llega un SETTLEMENT_COMPLETED
    Comprobamos:
    - estado final de payment_session
    - llamadas a contract_engine
    - auditoría generada
    """
    audit_repo = InMemoryAuditRepository()
    orchestrator = WalletOrchestrator(audit_repo=audit_repo)

    # 1) Simulamos webhook DEPOSIT_OK
    dep_event = DepositOkEvent(
        fintech_operation_id="fin_deposit_1",
        session_id="sess_1",
        user_id="user_1",
        amount=25.0,
        currency="EUR",
        raw_payload={"dummy": True},
        received_at=datetime.utcnow(),
    )
    orchestrator.handle_deposit_ok(dep_event)

    # 2) Simulamos webhook SETTLEMENT_COMPLETED
    set_event = SettlementCompletedEvent(
        fintech_operation_id="fin_settle_1",
        session_id="sess_1",
        provider_id="prov_1",
        amount=100.0,
        currency="EUR",
        raw_payload={"dummy": True},
        received_at=datetime.utcnow(),
    )
    orchestrator.handle_settlement_completed(set_event)

    # --- Asserts de ejemplo (ajusta según la lógica real) ---

    # Debe haberse llamado contract_engine.on_participant_funded
    assert len(dummy_contract_engine["on_participant_funded"]) == 1

    # Debe haberse llamado contract_engine.on_settlement_completed
    assert len(dummy_contract_engine["on_settlement_completed"]) == 1

    # Auditoría debería haber registrado al menos 2 eventos
    actions = [e["action"] for e in audit_repo.events]
    assert "DEPOSIT_OK" in actions
    assert "SETTLEMENT_COMPLETED" in actions
