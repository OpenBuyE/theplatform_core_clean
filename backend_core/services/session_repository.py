import streamlit as st

from backend_core.services.supabase_client import fetch_rows, update_row
from backend_core.services.audit_repository import log_action
from backend_core.services.context import (
    get_current_user,
    get_current_org,
    get_current_permissions
)


def _require_org_or_empty() -> str | None:
    """
    Devuelve organization_id si existe.
    Si no, muestra advertencia y devuelve None → devolvemos lista vacía.
    """
    org_id = get_current_org()
    if not org_id:
        st.warning("Selecciona una organización para continuar.")
        return None
    return org_id


def get_sessions() -> list[dict]:
    org_id = _require_org_or_empty()
    if not org_id:
        return []

    params = {
        "select": "*",
        "status": "eq.parked",
        "organization_id": f"eq.{org_id}",
    }
    return fetch_rows("sessions", params)


def get_active_sessions() -> list[dict]:
    org_id = _require_org_or_empty()
    if not org_id:
        return []

    params = {
        "select": "*",
        "status": "in.(active,open,running)",
        "organization_id": f"eq.{org_id}",
    }
    return fetch_rows("sessions", params)


def get_chains() -> list[dict]:
    org_id = _require_org_or_empty()
    if not org_id:
        return []

    params = {
        "select": "*",
        "chain_group_id": "not.is.null",
        "organization_id": f"eq.{org_id}",
    }
    return fetch_rows("sessions", params)


def activate_session(session_id: str) -> dict:
    org_id = get_current_org()
    user_id = get_current_user()

    if not org_id:
        raise RuntimeError("No hay organización activa.")
    if not user_id:
        raise RuntimeError("No hay usuario activo.")
    if "session.activate" not in get_current_permissions():
        raise RuntimeError("No tienes permisos para activar sesiones.")

    patch = {
        "status": "active",
        "organization_id": org_id,
    }

    updated = update_row("sessions", session_id, patch)

    if updated is None:
        raise RuntimeError("No se pudo actualizar la sesión en Supabase.")

    # Registro de auditoría
    log_action(
        action="activate_session",
        session_id=session_id,
        performed_by=user_id,
        metadata={"new_status": "active"}
    )

    return updated




