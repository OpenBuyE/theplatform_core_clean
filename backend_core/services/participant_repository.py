import streamlit as st
import requests

from backend_core.services.supabase_client import fetch_rows, update_row
from backend_core.services.context import get_current_org, get_current_user
from backend_core.services.audit_repository import log_action
from backend_core.services.adjudicator_engine import adjudicate_session

SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = st.secrets["SUPABASE_SERVICE_ROLE"]


def _headers() -> dict:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


# ---------------------------------------------------
#   PARTICIPANTES / COMPRADORES
# ---------------------------------------------------

def add_participant(session_id: str, amount: float, price: float, quantity: int = 1):
    """
    Registra un comprador en una sesión y actualiza el aforo.

    Regla clave:
      - Cada participante suma 1 en pax_registered
      - Si pax_registered == capacity → se dispara la operativa determinista
        (adjudicación inmediata) y la sesión se cierra.
    """
    org_id = get_current_org()
    user_id = get_current_user()

    if not org_id or not user_id:
        st.error("No hay organización o usuario activo para registrar el comprador.")
        return None

    url = f"{SUPABASE_URL}/rest/v1/session_participants"

    payload = {
        "session_id": session_id,
        "user_id": user_id,
        "organization_id": org_id,
        "amount": amount,
        "price": price,
        "quantity": quantity,
    }

    try:
        resp = requests.post(url, headers=_headers(), json=payload, timeout=10)

        if not resp.ok:
            st.error(f"Error al registrar comprador: {resp.text}")
            return None

        data = resp.json()
        participant = data[0] if isinstance(data, list) and data else data

        # Actualizar aforo y, si se completa, disparar adjudicación determinista
        _increment_pax_and_maybe_adjudicate(session_id)

        return participant

    except Exception as e:
        st.error(f"Error al registrar comprador: {e}")
        return None


def list_participants(session_id: str) -> list[dict]:
    params = {
        "select": "*, users(name,email)",
        "session_id": f"eq.{session_id}",
        "order": "created_at.asc",
    }
    return fetch_rows("session_participants", params)


# ---------------------------------------------------
#   AFORO: pax_registered + adjudicación
# ---------------------------------------------------

def _increment_pax_and_maybe_adjudicate(session_id: str):
    """
    Incrementa pax_registered.
    Si pax_registered == capacity → dispara adjudicación determinista.

    El cierre de sesión por tiempo (5 días sin completar aforo)
    lo gestiona session_engine.process_expired_sessions().
    """
    rows = fetch_rows(
        "sessions",
        {
            "select": "*",
            "id": f"eq.{session_id}",
        }
    )

    if not rows:
        st.error("No se encontró la sesión para actualizar el aforo.")
        return

    session = rows[0]
    current_pax = session.get("pax_registered") or 0
    capacity = session.get("capacity") or 0

    new_pax = current_pax + 1

    patch = {
        "pax_registered": new_pax,
    }

    update_row("sessions", session_id, patch)

    # Si no hay capacidad definida, no podemos aplicar la lógica de grupo completo
    if capacity <= 0:
        return

    # Si se ha completado el aforo → adjudicación determinista inmediata
    if new_pax >= capacity:
        log_action(
            action="session_full_capacity_reached",
            session_id=session_id,
            performed_by=get_current_user() or "system",
            metadata={
                "pax_registered": new_pax,
                "capacity": capacity,
            },
        )

        adjudicate_session(session_id)


# ---------------------------------------------------
#   ADJUDICACIÓN (bandera en participantes)
# ---------------------------------------------------

def mark_as_adjudicated(participant_id: str) -> dict | None:
    """
    Marca a un comprador como adjudicatario determinista.
    """
    from datetime import datetime
    import pytz

    now = datetime.now(pytz.utc).isoformat()
    patch = {
        "is_awarded": True,
        "awarded_at": now,
    }

    try:
        updated = update_row("session_participants", participant_id, patch)
        return updated
    except Exception as e:
        st.error(f"Error al marcar adjudicatario: {e}")
        return None
