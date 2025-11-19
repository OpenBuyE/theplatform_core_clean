import streamlit as st

from backend_core.services.supabase_client import fetch_rows, update_row
from backend_core.services.audit_repository import log_action


def _get_current_user() -> str:
    """
    Identifica al usuario actual.
    De momento usamos un identificador simple en el panel.
    En el SaaS futuro esto vendrá del sistema de autenticación.
    """
    return st.session_state.get("current_user", "panel_operator")


def _get_current_org_id() -> str | None:
    """
    Devuelve la organización activa desde la sesión de Streamlit.
    Es la base del multi-tenant: todas las queries irán filtradas por esto.
    """
    return st.session_state.get("organization_id")


def get_sessions() -> list[dict]:
    """
    Devuelve las sesiones en estado 'parked' de la organización activa.
    """
    org_id = _get_current_org_id()
    if not org_id:
        st.warning("Selecciona una organización para ver el parque de sesiones.")
        return []

    params = {
        "select": "*",
        "status": "eq.parked",
        "organization_id": f"eq.{org_id}",
    }
    return fetch_rows("sessions", params)


def get_active_sessions() -> list[dict]:
    """
    Devuelve las sesiones activas de la organización activa.
    Consideramos activos: active, open, running.
    """
    org_id = _get_current_org_id()
    if not org_id:
        st.warning("Selecciona una organización para ver las sesiones activas.")
        return []

    params = {
        "select": "*",
        "status": "in.(active,open,running)",
        "organization_id": f"eq.{org_id}",
    }
    return fetch_rows("sessions", params)


def get_chains() -> list[dict]:
    """
    Devuelve las sesiones con cadena operativa asociada
    (chain_group_id no nulo) de la organización activa.
    """
    org_id = _get_current_org_id()
    if not org_id:
        st.warning("Selecciona una organización para ver las cadenas operativas.")
        return []

    params = {
        "select": "*",
        "chain_group_id": "not.is.null",
        "organization_id": f"eq.{org_id}",
    }
    return fetch_rows("sessions", params)


def activate_session(session_id: str) -> dict:
    """
    Cambia una sesión a estado 'active' y registra auditoría.

    Multi-tenant:
    - La sesión se actualiza (status + opcionalmente organization_id)
    - Se registra log en audit_logs ligado a la misma organización
    """
    org_id = _get_current_org_id()
    if not org_id:
        raise RuntimeError(
            "No hay organización activa. "
            "Selecciona una organización antes de activar sesiones."
        )

    patch = {
        "status": "active",
        # Opcional pero recomendable: asegurar que la sesión quede ligada a esta organización
        "organization_id": org_id,
    }

    updated = update_row("sessions", session_id, patch)

    if updated is None:
        # Esto será capturado por el try/except en la vista
        raise RuntimeError("No se pudo actualizar la sesión en Supabase.")

    # Registrar auditoría
    log_action(
        action="activate_session",
        session_id=session_id,
        performed_by=_get_current_user(),
        metadata={"new_status": "active"},
    )

    return updated



