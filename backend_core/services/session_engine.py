import streamlit as st
from datetime import datetime
import pytz

from backend_core.services.supabase_client import fetch_rows, update_row
from backend_core.services.adjudicator_engine import adjudicate_session
from backend_core.services.audit_repository import log_action


def _now():
    return datetime.now(pytz.utc).isoformat()


# -------------------------------------------------------------------
#  OBTENER SESIONES EXPIRADAS
# -------------------------------------------------------------------

def _get_expired_sessions():
    """
    Devuelve sesiones con expires_at < ahora y estado = active.
    """
    params = {
        "select": "*",
        "status": "eq.active",
        "expires_at": f"lt.{_now()}"
    }
    return fetch_rows("sessions", params)


# -------------------------------------------------------------------
#  PROCESAR EXPIRACIÓN + ADJUDICACIÓN AUTOMÁTICA
# -------------------------------------------------------------------

def _finish_session(session: dict):
    """
    1. Cambia status → finished
    2. Activa adjudicación determinista
    3. Registra auditoría
    """
    sid = session["id"]

    # Cambiar estado
    patch = {
        "status": "finished",
        "finished_at": _now()
    }

    update_row("sessions", sid, patch)

    # Adjudicación determinista
    adjudication = adjudicate_session(sid)

    # Auditoría
    log_action(
        action="session_finished",
        session_id=sid,
        performed_by="system_auto",
        metadata={"adjudication": adjudication}
    )

    return adjudication


# -------------------------------------------------------------------
#  MOTOR PÚBLICO (SE EJECUTA EN app.py)
# -------------------------------------------------------------------

def process_expired_sessions():
    """
    Este motor corre automáticamente cada vez que se carga el panel.
    Revisa sesiones expiradas → las finaliza → adjudica.
    """
    try:
        expired = _get_expired_sessions()

        if not expired:
            return

        for session in expired:
            _finish_session(session)

    except Exception as e:
        st.error(f"Error en motor automático: {str(e)}")

