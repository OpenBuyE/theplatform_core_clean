from backend_core.models.session import Session
from backend_core.services.session_repository import SessionRepository
from datetime import datetime, timedelta


def test_session_repository_basic():
    repo = SessionRepository()

    # Crear sesiones
    s1 = Session(operator_id="OP-A", supplier_id="SUP-1", amount=1000)
    s2 = Session(operator_id="OP-B", supplier_id="SUP-2", amount=5000)

    repo.add(s1)
    repo.add(s2)

    assert len(repo.get_all()) == 2

    # Activar sesión
    repo.activate(s1.id)
    assert repo.get_by_id(s1.id).status == "active"

    # Programar sesión
    future = datetime.utcnow() + timedelta(days=1)
    repo.schedule(s2.id, future)
    assert repo.get_by_id(s2.id).status == "scheduled"

    print("TEST OK: session repository works correctly")
