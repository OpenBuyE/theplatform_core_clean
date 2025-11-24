# tests/test_module_repository.py

from unittest.mock import MagicMock, patch

from backend_core.services import module_repository


def _fake_resp(data):
    return type("Resp", (), {"data": data})


@patch("backend_core.services.module_repository.table")
def test_list_all_modules_returns_active_modules(mock_table):
    qb = MagicMock()
    qb.select.return_value = qb
    qb.eq.return_value = qb
    qb.execute.return_value = _fake_resp(
        [
            {"id": "mod-1", "module_code": "DETERMINISTIC", "is_active": True},
            {"id": "mod-2", "module_code": "AUTO_EXPIRE", "is_active": True},
        ]
    )

    mock_table.return_value = qb

    mods = module_repository.list_all_modules()
    assert len(mods) == 2
    assert mods[0]["module_code"] == "DETERMINISTIC"
    mock_table.assert_called_once()  # se llamó a table("ca_modules")


@patch("backend_core.services.module_repository.table")
def test_assign_module_to_session_inserts_relation_when_not_existing(mock_table):
    # Para SESSION_MODULES_TABLE
    qb = MagicMock()
    qb.select.return_value = qb
    qb.eq.return_value = qb
    qb.execute.return_value = _fake_resp([])  # no había relación previa
    qb.insert.return_value = qb

    mock_table.return_value = qb

    module_repository.assign_module_to_session("sess-1", "mod-1")

    # Debe haber hecho un insert en ca_session_modules
    assert qb.insert.called
    insert_args, insert_kwargs = qb.insert.call_args
    payload = insert_args[0]
    assert payload["session_id"] == "sess-1"
    assert payload["module_id"] == "mod-1"


@patch("backend_core.services.module_repository.table")
def test_get_module_for_session_fetches_module(mock_table):
    # 1) respuesta de ca_session_modules
    qb_rel = MagicMock()
    qb_rel.select.return_value = qb_rel
    qb_rel.eq.return_value = qb_rel
    qb_rel.single.return_value = qb_rel
    qb_rel.execute.return_value = _fake_resp({"session_id": "sess-1", "module_id": "mod-1"})

    # 2) respuesta de ca_modules
    qb_mod = MagicMock()
    qb_mod.select.return_value = qb_mod
    qb_mod.eq.return_value = qb_mod
    qb_mod.single.return_value = qb_mod
    qb_mod.execute.return_value = _fake_resp(
        {"id": "mod-1", "module_code": "DETERMINISTIC", "is_active": True}
    )

    # table(...) devuelve objetos distintos según primera / segunda llamada
    mock_table.side_effect = [qb_rel, qb_mod]

    m = module_repository.get_module_for_session("sess-1")
    assert m is not None
    assert m["module_code"] == "DETERMINISTIC"
