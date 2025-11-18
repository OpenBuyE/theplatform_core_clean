from backend_core.services.session_repository import SessionRepository
from backend_core.models.session import Session
from datetime import datetime, timedelta

# Repositorio único en toda la app
repo = SessionRepository()


def load_seed_sessions():
    """
    Carga inicial de sesiones para demostrar el dashboard.
    Solo se ejecuta una vez.
    """

    # Evitar duplicados si ya hay datos cargados
    if repo.get_all():
        return repo

    sessions = [
        Session(operator_id="OP-A", supplier_id="SUP-101", amount=12000),
        Session(operator_id="OP-B", supplier_id="SUP-202", amount=34000),
        Session(operator_id="OP-A", supplier_id="SUP-303", amount=18000),
    ]

    # Activar una sesión
    active = Session(operator_id="OP-A", supplier_id="SUP-404", amount=9000, status="active")
    active.activated_at = datetime.utcnow()
    sessions.append(active)

    # Programada
    scheduled = Session(operator_id="OP-A", supplier_id="SUP-505", amount=25000, status="scheduled")
    scheduled.scheduled_for = datetime.utcnow() + timedelta(days=2)
    sessions.append(scheduled)

    # Cargar todas
    for s in sessions:
        repo.add(s)

    return repo


# Cargar automáticamente al importar
load_seed_sessions()

