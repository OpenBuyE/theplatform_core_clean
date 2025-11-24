# tests/test_module_repository.py

from backend_core.services.module_repository import (
    list_all_modules,
    get_module_for_session,
    assign_module_to_session,
)

from tests.factories.module_factory import fake_module


def test_list_all_modules(mock_supabase):
    modules = list_all_modules()
    assert isinstance(modules, list)


def test_assign_and_get_module(mock_supabase):
    # Insertamos módulo fake
    assign_module_to_session("sess-001", "mod-001")

    result = get_module_for_session("sess-001")
    assert result is not None
    assert "module_id" in result
