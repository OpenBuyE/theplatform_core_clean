import streamlit as st
from datetime import datetime, timedelta
import pytz

from backend_core.services.supabase_client import fetch_rows, update_row
from backend_core.services.audit_repository import log_action
from backend_core.services.context import get_current_org, get_current_user


# --------------------------------------------------------------------
#   Utilidades internas
# --------------------------------------------------------------------

def _now():
    """Hora actual con zona horaria del servidor."""
    return datetime.now(pytz.utc)


def _fetch_active_in_series(series_id: str, org_id: str):
    """
    Devuelve la sesión activa de la serie actual.
    """
    params = {
        "select": "*",
        "series_id": f"eq.{series_id}",
        "organization_id": f"eq.{org_id}",
        "status": "in.(active,running,open)",
    }
    rows = fetch_rows("sessions", params)
    if rows:
        return rows[0]
    return None


def _fetch_next_sequence(series_id: str, org_id: str, current_seq: int):
    """
    Devuelve la siguiente sesión parked en la secuencia.
    """
    params = {
        "select": "*",
        "series_id": f"eq.{series_id}",
        "organization_id": f"eq.{org_id}",
        "sequence_number": f"eq.{current_seq + 1}",
        "status": "eq.parked",
    }
    rows = fetch_rows("sessions", params)
    if rows:
        return rows[0]
    return None


# --------------------------------------------------------------------
#   Activación automática de la siguiente sesión
# --------------------------------------------------------------------

def activate_next_in_series(series_id: str, current_sequence: int) -> dict | None:
    """
    Activa la siguiente sesión en una serie rolling, si existe.
    """
    org_id = get_current_org()
    user_id = get_current_user() or "system"

    next_session = _fetch_next_sequence(series_id, org_id, current_sequence)
    if not next_session:
        # No hay más sesiones → fin de serie
        return None

    session_id = next_session["id"]

    patch = {
        "status": "active",
        "activated_at": _now().isoformat(),
        "expires_at": (_now() + timedelta(days=5)).isoformat(),
        "organization_id": org_id,
    }

    updated = update_row("sessions", session_id, patch)

    # Auditoría
    log_action(
        action="auto_activate_session",
        session_id=session_id,
        performed_by=user_id,
        metadata={"reason": "rolling_series"},
    )

    return updated


# --------------------------------------------------------------------
#   Avanzar una serie manual o automáticamente
# --------------------------------------------------------------------

def advance_series(series_id: str) -> dict:
    """
    Realiza la secuencia completa de avance:
      - Marca la sesión activa como finalizada
      - Activa la siguiente
      - Devuelve la info

    Esto se usará cuando:
      1) una sesión expira
      2) adjudicator cierre la sesión
      3) manualmente desde dashboard (futuro)
    """
    org_id = get_current_org()
    user_id = get_current_user() or "system"

    active = _fetch_active_in_series(series_id, org_id)

    if not active:
        return {"message": "No active session in series.", "series_id": series_id}

    current_id = active["id"]
    current_seq = active.get("sequence_number", 0)

    # 1️⃣ Marcar la actual como finalizada
    update_row("sessions", current_id, {"status": "finished"})

    log_action(
        action="finish_session",
        session_id=current_id,
        performed_by=user_id,
        metadata={"reason": "advance_series"},
    )

    # 2️⃣ Activar siguiente
    activated = activate_next_in_series(series_id, current_seq)

    return {
        "finished_id": current_id,
        "activated": activated,
        "series_id": series_id,
    }


# --------------------------------------------------------------------
#   Procesar expiraciones automáticas
# --------------------------------------------------------------------

def process_expired_sessions():
    """
    Busca sesiones activas cuya expires_at < now()
    y las avanza si son parte de una serie rolling.
    """
    org_id = get_current_org()
    user_id = get_current_user() or "system"

    params = {
        "select": "*",
        "organization_id": f"eq.{org_id}",
        "status": "in.(active,running,open)",
    }
    active_sessions = fetch_rows("sessions", params)

    now = _now()

    for session in active_sessions:
        exp = session.get("expires_at")
        if not exp:
            continue

        exp_dt = datetime.fromisoformat(exp)

        if exp_dt < now:
            # Expirada → cerramos y avanzamos serie
            session_id = session["id"]
            series_id = session.get("series_id")
            seq = session.get("sequence_number")

            # Cerrar sesión
            update_row("sessions", session_id, {"status": "finished"})

            log_action(
                action="session_expired",
                session_id=session_id,
                performed_by=user_id,
                metadata={"expired_at": exp},
            )

            # ¿Pertenece a una serie rolling?
            if series_id:
                activate_next_in_series(series_id, seq)
