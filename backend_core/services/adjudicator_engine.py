from datetime import datetime, timedelta
import pytz

from backend_core.services.participant_repository import (
    list_participants,
    mark_as_adjudicated,
)
from backend_core.services.audit_repository import log_action
from backend_core.services.context import get_current_user
from backend_core.services.supabase_client import fetch_rows, update_row


def _now():
    return datetime.now(pytz.utc)


def _get_next_in_series(session: dict) -> dict | None:
    series_id = session.get("series_id")
    org_id = session.get("organization_id")
    seq = session.get("sequence_number")

    if not series_id or org_id is None or seq is None:
        return None

    params = {
        "select": "*",
        "series_id": f"eq.{series_id}",
        "organization_id": f"eq.{org_id}",
        "sequence_number": f"eq.{seq + 1}",
        "status": "eq.parked",
    }
    rows = fetch_rows("sessions", params)
    if rows:
        return rows[0]
    return None


def _activate_session(session: dict):
    sid = session["id"]
    now = _now()
    patch = {
        "status": "active",
        "activated_at": now.isoformat(),
        "expires_at": (now + timedelta(days=5)).isoformat(),
    }
    update_row("sessions", sid, patch)

    log_action(
        action="session_auto_activated_from_series",
        session_id=sid,
        performed_by="system",
        metadata={"reason": "previous_session_adjudicated"},
    )


def adjudicate_session(session_id: str) -> dict:
    """
    Motor determinista de adjudicación.

    Regla clave de Compra Abierta:
      - Solo se adjudica si el aforo está COMPLETO:
            pax_registered >= capacity (>0)
      - Cuando se llena el grupo, se adjudica inmediatamente
        y se cierra la sesión.
      - Si hay serie configurada, se activa la siguiente sesión limpia.
    """
    # 1) Leer sesión
    sessions = fetch_rows(
        "sessions",
        {
            "select": "*",
            "id": f"eq.{session_id}",
        },
    )

    if not sessions:
        return {
            "session_id": session_id,
            "adjudicated": None,
            "reason": "session_not_found",
        }

    session = sessions[0]
    pax = session.get("pax_registered") or 0
    capacity = session.get("capacity") or 0

    if capacity <= 0:
        return {
            "session_id": session_id,
            "adjudicated": None,
            "reason": "capacity_not_defined",
        }

    if pax < capacity:
        # Grupo aún incompleto → no se puede adjudicar
        return {
            "session_id": session_id,
            "adjudicated": None,
            "reason": "capacity_not_full",
            "pax_registered": pax,
            "capacity": capacity,
        }

    # 2) Leer participantes
    participants = list_participants(session_id)
    if not participants:
        return {
            "session_id": session_id,
            "adjudicated": None,
            "reason": "no_participants",
        }

    # 3) Regla determinista actual (placeholder):
    #    el primer comprador registrado es el adjudicatario.
    #    Más adelante se puede reemplazar por el algoritmo
    #    definido en la Memoria Técnica (semilla pública, etc.).
    first = participants[0]

    awarded = mark_as_adjudicated(first["id"])

    # 4) Cerrar sesión
    update_row(
        "sessions",
        session_id,
        {
            "status": "finished",
            "finished_at": _now().isoformat(),
        },
    )

    # 5) Avanzar serie (sesión limpia siguiente)
    next_session = _get_next_in_series(session)
    if next_session:
        _activate_session(next_session)

    # 6) Auditoría
    log_action(
        action="session_adjudicated",
        session_id=session_id,
        performed_by=get_current_user() or "system_auto",
        metadata={
            "adjudicated_to_user_id": first["user_id"],
            "participant_id": first["id"],
            "pax_registered": pax,
            "capacity": capacity,
            "rule": "first_participant_full_capacity",
            "awarded_at": _now().isoformat(),
        },
    )

    return {
        "session_id": session_id,
        "adjudicated": awarded,
        "rule": "first_participant_full_capacity",
    }
