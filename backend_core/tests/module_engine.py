# tests/test_module_engine.py

from backend_core.services.module_engine import module_engine
from tests.factories.session_factory import fake_session
from tests.factories.module_factory import fake_module


def test_deterministic_supported():
    m = fake_module(module_code="DETERMINISTIC")
    assert module_engine.supports_adjudication(m) is True


def test_prelaunch_no_activation():
    m = fake_module(module_code="PRELAUNCH")
    result = module_engine.can_activate_session(m)
    assert result is False
