import streamlit as st
from backend_core.services.session_repository import SessionRepository
from backend_core.dashboard.ui.components import session_card

repo = SessionRepository()  # repositorio en memoria temporal


def render_park_sessions():
    st.subheader("🅿️ Parque de Sesiones")

    parked = repo.get_by_status("parked")

    if not parked:
        st.info("No hay sesiones en estado 'parked'.")
        return

    for s in parked:
        session_card(s)
