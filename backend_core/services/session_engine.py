import streamlit as st
from datetime import datetime
import pytz

from backend_core.services.supabase_client import fetch_rows, update_row
from backend_core.services.audit_repository import log_action


def _now():
    return datetime.now(pytz.utc)


# ---------------------------------------------------------
#   HELPER: siguiente sesión en serie (rolling)
# ---------------------------------------------------------

def _get_next_in_series(session: dict) -> dict | None:
    """
    Busca la siguiente sesión 'parked' en la misma serie,
    con sequence_number = actual + 1.
    """
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
    """
    Activa una sesión (por ejemplo, la siguiente de la serie).
    """
    from datetime import timedelta

    sid = session["id"]
    now = _now()
    patch = {
        "status": "active",
        "activated_at": now.isoformat(),
        "expires_at": (now + timedelta(days=5)).isoformat(),
    }
    updated = update_row("sessions", sid, patch)

    log_action(
        action="session_auto_activated_from_series",
        session_id=sid,
        performed_by="system",
        metadata={"reason": "previous_session_finished"},
    )

    return updated


def _finish_session_without_award(session: dict, reason: str):
    """
    Marca la sesión como finalizada SIN adjudicación (grupo incompleto)
    y, si es de serie, lanza la siguiente.
    """
    sid = session["id"]

    patch = {
        "status": "finished",
        "finished_at": _now().isoformat(),
    }
    update_row("sessions", sid, patch)

    log_action(
        action="session_finished_without_award",
        session_id=sid,
        performed_by="system_auto",
        metadata={"reason": reason},
    )

    # Avance de serie (rolling)
    next_session = _get_next_in_series(session)
    if next_session:
        _activate_session(next_session)


# ---------------------------------------------------------
#   MOTOR PÚBLICO: procesar expiraciones (5 días)
# ---------------------------------------------------------

def process_expired_sessions():
    """
    Motor automático que se ejecuta cada vez que se carga el panel.
    Lógica:

    - Encuentra sesiones activas cuya expires_at < ahora.
    - Si NO completaron aforo (pax_registered < capacity) → se cierran sin adjudicatario
      y, si están dentro de una serie, se activa la siguiente sesión del parque.
    - La adjudicación determinista NO se hace aquí, sino en el momento
      en que el aforo se completa (participant_repository + adjudicator_engine).
    """
    try:
        now_iso = _now().isoformat()

        params = {
            "select": "*",
            "status": "eq.active",
            "expires_at": f"lt.{now_iso}",
        }
        expired = fetch_rows("sessions", params)

        if not expired:
            return

        for session in expired:
            capacity = session.get("capacity") or 0
            pax = session.get("pax_registered") or 0

            # Si por diseño correcto, una sesión con aforo completo
            # ya debería haber sido adjudicada y terminada.
            # Aquí solo tratamos los casos de grupo incompleto.
            if capacity > 0 and pax >= capacity:
                # No hacemos adjudicación aquí; asumimos que ya se hizo
                # cuando se llenó el aforo.
                continue

            _finish_session_without_award(
                session,
                reason="expired_without_full_capacity",
            )

    except Exception as e:
        st.error(f"Error en motor automático de expiraciones: {str(e)}")
