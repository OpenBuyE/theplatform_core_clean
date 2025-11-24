# tests/conftest.py

import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_audit_log():
    """
    Evita escribir logs reales en ca_audit_logs durante los tests.
    """
    with patch("backend_core.services.audit_repository.log_event") as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_wallet_orchestrator():
    """
    Evita que los tests llamen a integraciones de wallet/fintech reales.
    """
    with patch("backend_core.services.wallet_orchestrator.wallet_orchestrator") as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_contract_engine_instance():
    """
    Evita efectos secundarios en el motor contractual real.
    Sigue permitiendo verificar que se invocan sus métodos.
    """
    with patch("backend_core.services.contract_engine.contract_engine") as mock:
        yield mock
