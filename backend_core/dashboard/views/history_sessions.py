"""
history_sessions.py
Vista de sesiones finalizadas (finished)
"""

import streamlit as st
from backend_core.services.session_repository import session_repository
from backend_core.services.participant_repository import participant_repository


def render_history():
    st.title("📘 Historial de Sesiones Finalizadas")

    sessions = session_repository.get_sessions(status="finished", limit=200)

    if not sessions:
        st.info("No hay sesiones finalizadas todavía.")
        return

    for s in sessions:
        with st.expander(f"📘 Sesión {s['id']} — Producto {s['product_id']}"):
            st.write("**Estado:**", s["status"])
            st.write("**Aforo:**", f"{s['pax_registered']} / {s['capacity']}")
            st.write("**Serie:**", s["series_id"])
            st.write("**Sequence:**", s["sequence_number"])
            st.write("**Activada:**", s.get("activated_at"))
            st.write("**Finalizada:**", s.get("finished_at"))

            st.markdown("---")

            st.subheader("👥 Participantes")
            parts = participant_repository.get_participants_by_session(s["id"])
            st.dataframe(parts)

