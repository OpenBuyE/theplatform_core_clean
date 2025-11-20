from datetime import datetime
import pytz

from backend_core.services.participant_repository import (
    list_participants,
    mark_as_adjudicated,
)
from backend_core.services.audit_repository import log_action
from backend_core.services.context import get_current_user


# -------------------------------------------------------------
#   MOTOR DETERMINISTA DE ADJUDICACIÓN
# -------------------------------------------------------------

def adjudicate_session(session_id: str) -> dict:
    """
    Regla determinista actual:
    
    El COMPRADOR ADJUDICATARIO es el primer participante registrado
    (ordenado por created_at) que cumple con las condiciones siguientes:

    - La sesión está finalizada (validación en vista futura)
    - La cantidad o importe puede usarse como criterio en el futuro
    """

    participants = list_participants(session_id)
    if not participants:
        return {
            "session_id": session_id,
            "adjudicated": None,
            "reason": "No participants"
        }

    # ⭐ Regla determinista base:
    # "El primer participante es el adjudicatario"
    # (si hubiera reglas económicas más complejas, se implementan aquí)
    first = participants[0]

    awarded = mark_as_adjudicated(first["id"])

    # Auditoría
    log_action(
        action="session_adjudicated",
        session_id=session_id,
        performed_by=get_current_user(),
        metadata={
            "adjudicated_to": first["user_id"],
            "participant_id": first["id"],
            "awarded_at": datetime.now(pytz.utc).isoformat()
        }
    )

    return {
        "session_id": session_id,
        "adjudicated": awarded,
        "rule": "first_participant_deterministic"
    }
