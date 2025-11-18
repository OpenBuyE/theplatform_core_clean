import streamlit as st
from backend_core.services.session_repository import SessionRepository
from backend_core.dashboard.ui.components import session_card

repo = SessionRepository()


def render_active_sessions():
    st.subheader("⚡ Sesiones Activas")

    active = repo.get_by_status("active")

    if not active:
        st.info("No hay sesiones activas.")
        return

    for s in active:
        session_card(s)
