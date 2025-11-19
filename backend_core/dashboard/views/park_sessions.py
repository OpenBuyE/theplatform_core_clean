import streamlit as st
from backend_core.services.session_repository import SessionRepository


def render_park_sessions():
    st.subheader("🅿️ Parque de Sesiones")

    repo = SessionRepository()
    sessions = repo.get_parked()

    if not sessions:
        st.info("No hay sesiones parked en Supabase.")
        return

    for s in sessions:
        st.markdown(f"**ID:** {s.id}")
        st.markdown(f"Producto: {s.product_id}")
        st.markdown(f"Operador: {s.operator_code}")
        st.markdown(f"Estado: `{s.status}`")
        st.markdown(f"Importe: {s.amount} €")
        st.markdown("---")


