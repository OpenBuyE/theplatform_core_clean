# tests/test_contract_engine_with_modules.py

from unittest.mock import patch, MagicMock

from backend_core.services.contract_engine import contract_engine


def _fake_session():
    return {"id": "sess-1", "status": "finished"}


# -----------------------------------------------------------
# START CONTRACT
# -----------------------------------------------------------

@patch("backend_core.services.contract_engine.init_payment_session")
@patch("backend_core.services.contract_engine.get_module_for_session")
@patch("backend_core.services.contract_engine.get_session_by_id")
def test_start_contract_initializes_payment_for_deterministic(
    mock_get_session, mock_get_module, mock_init_payment
):
    mock_get_session.return_value = _fake_session()
    mock_get_module.return_value = {"module_code": "DETERMINISTIC"}

    contract_engine.start_contract("sess-1")

    mock_init_payment.assert_called_once_with("sess-1")


@patch("backend_core.services.contract_engine.init_payment_session")
@patch("backend_core.services.contract_engine.get_module_for_session")
@patch("backend_core.services.contract_engine.get_session_by_id")
def test_start_contract_skips_payment_for_non_deterministic(
    mock_get_session, mock_get_module, mock_init_payment
):
    mock_get_session.return_value = _fake_session()
    mock_get_module.return_value = {"module_code": "AUTO_EXPIRE"}

    contract_engine.start_contract("sess-1")

    mock_init_payment.assert_not_called()


# -----------------------------------------------------------
# DEPOSIT OK
# -----------------------------------------------------------

@patch("backend_core.services.contract_engine.update_payment_state")
@patch("backend_core.services.contract_engine.get_module_for_session")
@patch("backend_core.services.contract_engine.get_session_by_id")
def test_deposit_ok_updates_state_for_deterministic(
    mock_get_session, mock_get_module, mock_update_state
):
    mock_get_session.return_value = _fake_session()
    mock_get_module.return_value = {"module_code": "DETERMINISTIC"}

    contract_engine.on_deposit_ok("sess-1")

    mock_update_state.assert_called_once_with("sess-1", "DEPOSITS_OK")


@patch("backend_core.services.contract_engine.update_payment_state")
@patch("backend_core.services.contract_engine.get_module_for_session")
@patch("backend_core.services.contract_engine.get_session_by_id")
def test_deposit_ok_skips_state_for_non_deterministic(
    mock_get_session, mock_get_module, mock_update_state
):
    mock_get_session.return_value = _fake_session()
    mock_get_module.return_value = {"module_code": "PRELAUNCH"}

    contract_engine.on_deposit_ok("sess-1")

    mock_update_state.assert_not_called()


# -----------------------------------------------------------
# SETTLEMENT COMPLETED
# -----------------------------------------------------------

@patch("backend_core.services.contract_engine.update_payment_state")
@patch("backend_core.services.contract_engine.get_module_for_session")
@patch("backend_core.services.contract_engine.get_session_by_id")
def test_settlement_completed_updates_state_for_deterministic(
    mock_get_session, mock_get_module, mock_update_state
):
    mock_get_session.return_value = _fake_session()
    mock_get_module.return_value = {"module_code": "DETERMINISTIC"}

    contract_engine.on_settlement_completed("sess-1")

    mock_update_state.assert_called_once_with("sess-1", "SETTLED")
