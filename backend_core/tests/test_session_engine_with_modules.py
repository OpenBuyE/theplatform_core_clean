# tests/test_session_engine_with_modules.py

from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from backend_core.services.session_engine import session_engine


def _fake_session(status="finished", expires_at=None):
    return {
        "id": "sess-1",
        "series_id": "series-001",
        "status": status,
        "expires_at": expires_at,
    }


# -----------------------------------------------------------
# ROLLING
# -----------------------------------------------------------

@patch("backend_core.services.session_engine.get_next_session_in_series")
@patch("backend_core.services.session_engine.update_session_status")
@patch("backend_core.services.session_engine.get_module_for_session")
def test_on_session_finished_triggers_rolling_for_deterministic(
    mock_get_module, mock_update_status, mock_get_next
):
    mock_get_module.return_value = {"module_code": "DETERMINISTIC"}
    mock_get_next.return_value = {"id": "sess-2"}

    session_engine.on_session_finished("sess-1")

    mock_get_next.assert_called_once_with("sess-1")
    mock_update_status.assert_called_once_with("sess-2", "active")


@patch("backend_core.services.session_engine.get_next_session_in_series")
@patch("backend_core.services.session_engine.update_session_status")
@patch("backend_core.services.session_engine.get_module_for_session")
def test_on_session_finished_no_rolling_for_auto_expire(
    mock_get_module, mock_update_status, mock_get_next
):
    mock_get_module.return_value = {"module_code": "AUTO_EXPIRE"}

    session_engine.on_session_finished("sess-1")

    mock_get_next.assert_not_called()
    mock_update_status.assert_not_called()


# -----------------------------------------------------------
# EXPIRACIÓN
# -----------------------------------------------------------

@patch("backend_core.services.session_engine.finish_session")
@patch("backend_core.services.session_engine.get_module_for_session")
@patch("backend_core.services.session_engine.get_session_by_id")
def test_expire_if_needed_marks_session_finished_when_past_expiry(
    mock_get_session, mock_get_module, mock_finish
):
    expires_at = (datetime.utcnow() - timedelta(days=1)).isoformat()
    mock_get_session.return_value = _fake_session(expires_at=expires_at)
    mock_get_module.return_value = {"module_code": "AUTO_EXPIRE"}

    session_engine.expire_if_needed("sess-1")

    mock_finish.assert_called_once_with("sess-1")


@patch("backend_core.services.session_engine.finish_session")
@patch("backend_core.services.session_engine.get_module_for_session")
@patch("backend_core.services.session_engine.get_session_by_id")
def test_expire_if_needed_does_nothing_if_no_expires_at(
    mock_get_session, mock_get_module, mock_finish
):
    mock_get_session.return_value = _fake_session(expires_at=None)

    session_engine.expire_if_needed("sess-1")

    mock_finish.assert_not_called()
