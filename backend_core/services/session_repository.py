from backend_core.services.supabase_client import fetch_rows, update_row
from backend_core.services.audit_repository import log_action
import streamlit as st


def _get_current_user() -> str:
    """
    Identifica al usuario actual.
    Para la versión interna de panel, devolveremos un identificador sencillo.
    En SaaS futuro, esto vendrá del sistema de autenticación.
    """
    return st.session_state.get("current_user", "panel_operator")


def get_sessions() -> list[dict]:
    params = {
        "select": "*",
        "status": "eq.parked",
    }
    return fetch_rows("sessions", params)


def get_active_sessions() -> list[dict]:
    params = {
        "select": "*",
        "status": "in.(active,open,running)",
    }
    return fetch_rows("sessions", params)


def get_chains() -> list[dict]:
    params = {
        "select": "*",
        "chain_group_id": "not.is.null",
    }
    return fetch_rows("sessions", params)


def activate_session(session_id: str) -> dict:
    """
    Cambia una sesión a estado active y registra auditoría.
    """
    patch = {
        "status": "active"
    }

    updated = update_row("sessions", session_id, patch)

    if updated is None:
        raise RuntimeError("No se pudo actualizar la sesión en Supabase.")

    # Registrar auditoría
    log_action(
        action="activate_session",
        session_id=session_id,
        performed_by=_get_current_user(),
        metadata={"new_status": "active"}
    )

    return updated


