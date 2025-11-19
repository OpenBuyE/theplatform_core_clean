import streamlit as st
from backend_core.services.permission_repository import get_user_permissions


def get_current_user() -> str | None:
    """Obtiene el user_id activo dentro del panel."""
    return st.session_state.get("user_id")


def get_current_org() -> str | None:
    """Obtiene la organización activa."""
    return st.session_state.get("organization_id")


def get_current_permissions() -> set[str]:
    """Devuelve el conjunto de permisos efectivos del usuario para la organización."""
    user_id = get_current_user()
    org_id = get_current_org()

    if not user_id or not org_id:
        return set()

    return get_user_permissions(user_id, org_id)
