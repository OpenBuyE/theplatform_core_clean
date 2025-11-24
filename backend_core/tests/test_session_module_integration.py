# tests/test_session_module_integration.py

from backend_core.services.module_repository import assign_module_to_session
from backend_core.services.session_repository import get_session_by_id
from backend_core.services.module_repository import get_module_for_session


def test_session_has_assigned_module(mock_supabase):
    assign_module_to_session("sess-001", "mod-001")
    module = get_module_for_session("sess-001")
    assert module is not None
