# backend_core/dashboard/views/active_sessions.py

import streamlit as st
import requests

from backend_core.services.session_repository import (
    get_active_sessions,
    get_participants,
)
from backend_core.services.audit_repository import AuditRepository

API_BASE = "http://localhost:8000"   # Ajusta si usas otro host/puerto

audit = AuditRepository()


def render_active_sessions():
    st.title("Active Sessions")
    st.write("Gestión de sesiones activas, participantes y adjudicación.")

    sessions = get_active_sessions()

    if not sessions:
        st.info("No hay sesiones activas.")
        return

    for s in sessions:
        st.subheader(f"🟢 Sesión Activa: {s['id']}")
        st.write(f"- Product ID: {s['product_id']}")
        st.write(f"- Organization ID: {s['organization_id']}")
        st.write(f"- Capacity: {s['capacity']}")
        st.write(f"- Pax Registered: {s['pax_registered']}")
        st.write("---")

        st.write("👥 Participantes:")
        participants = get_participants(s["id"])

        if participants:
            st.json(participants)
        else:
            st.info("Sin participantes todavía.")

        # Añadir participante test (endpoint de debug opcional)
        if st.button(f"Añadir participante test a {s['id']}", key=f"add_pax_{s['id']}"):
            try:
                resp = requests.post(
                    f"{API_BASE}/internal/debug/add-test-participant",
                    json={"session_id": s["id"]},
                    timeout=8,
                )
                st.success(resp.json())
                audit.log(
                    action="TEST_PARTICIPANT_ADDED",
                    session_id=s["id"],
                    user_id=None,
                    metadata={},
                )
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error: {e}")

        # Forzar adjudicación (endpoint de debug opcional)
        if st.button(f"Forzar adjudicación {s['id']}", key=f"award_{s['id']}"):
            try:
                resp = requests.post(
                    f"{API_BASE}/internal/debug/force-award",
                    json={"session_id": s["id"]},
                    timeout=12,
                )
                st.success(resp.json())
                audit.log(
                    action="SESSION_FORCED_AWARD",
                    session_id=s["id"],
                    user_id=None,
                    metadata={},
                )
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error: {e}")

        st.divider()
