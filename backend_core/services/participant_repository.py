import streamlit as st
import requests
from datetime import datetime
import pytz

from backend_core.services.supabase_client import fetch_rows
from backend_core.services.context import get_current_org, get_current_user
from backend_core.services.supabase_client import update_row

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_SERVICE_ROLE"]


def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }


# ---------------------------------------------------
#   PARTICIPANTES – CRUD
# ---------------------------------------------------

def add_participant(session_id: str, amount: float, price: float, quantity: int = 1):
    """
    Añade un comprador (participante) a una sesión.
    """
    org = get_current_org()
    user = get_current_user()

    url = f"{SUPABASE_URL}/rest/v1/session_participants"

    payload = {
        "session_id": session_id,
        "user_id": user,
        "organization_id": org,
        "amount": amount,
        "price": price,
        "quantity": quantity,
    }

    resp = requests.post(url, headers=_headers(), json=payload)
    if not resp.ok:
        st.error(f"Error al registrar participante: {resp.text}")
        return None

    data = resp.json()
    return data[0] if isinstance(data, list) and data else data


def list_participants(session_id: str):
    params = {
        "select": "*, users(name,email)",
        "session_id": f"eq.{session_id}",
        "order": "created_at.asc",
    }
    return fetch_rows("session_participants", params)


# ---------------------------------------------------
#   ADJUDICACIÓN
# ---------------------------------------------------

def mark_as_adjudicated(participant_id: str):
    """
    Marca un participante como adjudicatario determinista.
    """
    now = datetime.now(pytz.utc).isoformat()

    patch = {
        "is_awarded": True,
        "awarded_at": now
    }

    updated = update_row("session_participants", participant_id, patch)
    return updated
