# tests/factories/module_factory.py

def fake_module(
    id="mod-001",
    module_code="DETERMINISTIC",
    name="Deterministic Core Module",
    description="Test deterministic module"
):
    return {
        "id": id,
        "module_code": module_code,
        "name": name,
        "description": description,
        "is_active": True,
    }
