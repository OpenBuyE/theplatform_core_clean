# tests/test_adjudicator_with_modules_advanced.py

from unittest.mock import patch, MagicMock
import pytest

from backend_core.services.adjudicator_engine import adjudicator_engine


def _fake_session():
    return {
        "id": "sess-1",
        "series_id": "series-001",
        "sequence_number": 1,
        "capacity": 3,
        "pax_registered": 3,
        "status": "active",
    }


def _fake_participants():
    return [
        {"id": "p1"},
        {"id": "p2"},
        {"id": "p3"},
    ]


# -----------------------------------------------------------
# MÓDULO NO DETERMINISTA
# -----------------------------------------------------------

@patch("backend_core.services.adjudicator_engine.get_module_for_session")
def test_adjudicator_rejects_non_deterministic_module(mock_get_module):
    mock_get_module.return_value = {"module_code": "AUTO_EXPIRE"}

    with pytest.raises(Exception):
        adjudicator_engine.adjudicate("sess-1")


# -----------------------------------------------------------
# FLOW COMPLETO CON MÓDULO DETERMINISTA
# -----------------------------------------------------------

@patch("backend_core.services.adjudicator_engine.contract_engine")
@patch("backend_core.services.adjudicator_engine.session_engine")
@patch("backend_core.services.adjudicator_engine.mark_session_finished")
@patch("backend_core.services.adjudicator_engine.mark_awarded")
@patch("backend_core.services.adjudicator_engine.get_seed_for_session")
@patch("backend_core.services.adjudicator_engine.get_participants_for_session")
@patch("backend_core.services.adjudicator_engine.get_session_by_id")
@patch("backend_core.services.adjudicator_engine.get_module_for_session")
def test_adjudicator_flow_for_deterministic_module(
    mock_get_module,
    mock_get_session,
    mock_get_participants,
    mock_get_seed,
    mock_mark_awarded,
    mock_mark_finished,
    mock_session_engine,
    mock_contract_engine,
):
    mock_get_module.return_value = {"module_code": "DETERMINISTIC"}
    mock_get_session.return_value = _fake_session()
    mock_get_participants.return_value = _fake_participants()
    mock_get_seed.return_value = {"public_seed": "TEST-SEED-123"}

    result = adjudicator_engine.adjudicate("sess-1")

    # Debe devolver info del adjudicatario
    assert "awarded" in result
    assert "index" in result
    assert "hash" in result

    # Debe marcar adjudicatario y sesión como finished
    assert mock_mark_awarded.called
    mock_mark_finished.assert_called_once_with("sess-1")

    # Debe disparar rolling y motor contractual
    mock_session_engine.on_session_finished.assert_called_once_with("sess-1")
    mock_contract_engine.start_contract.assert_called_once_with("sess-1")

