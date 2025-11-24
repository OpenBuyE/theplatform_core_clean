# tests/conftest.py

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# ==========================================================
# FIXTURAS GLOBALES
# ==========================================================

@pytest.fixture(autouse=True)
def mock_supabase():
    """
    Fake Supabase client para todos los tests.
    Nunca hace llamadas reales a Supabase.
    """
    with patch("backend_core.services.supabase_client.table") as mock_table_constructor:

        # Fake QueryBuilder con behavior controlado
        class FakeQuery:
            def __init__(self):
                self._data = []

            def select(self, *args, **kwargs):
                return self

            def eq(self, *args, **kwargs):
                return self

            def single(self):
                return self

            def order(self, *args, **kwargs):
                return self

            def insert(self, payload):
                self._data.append(payload)
                return self

            def update(self, payload):
                self._data.append(payload)
                return self

            def execute(self):
                return type("Resp", (), {"data": self._data})

        mock_table_constructor.return_value = FakeQuery()
        yield


@pytest.fixture(autouse=True)
def mock_audit():
    """Evita escribir auditoría real."""
    with patch("backend_core.services.audit_repository.log_event") as mock_log:
        yield mock_log


@pytest.fixture(autouse=True)
def mock_contract_engine():
    """Evita ejecutar contract_engine real."""
    with patch("backend_core.services.contract_engine.contract_engine") as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_wallet():
    """Evita correr wallet_orchestrator real."""
    with patch("backend_core.services.wallet_orchestrator.wallet_orchestrator") as mock:
        yield mock


@pytest.fixture
def fake_uuid():
    return "11111111-2222-3333-4444-555555555555"
