# backend_core/dashboard/views/park_sessions.py

import streamlit as st

from backend_core.services.session_repository import (
    create_parked_session,
    activate_session,
    get_parked_sessions,
)
from backend_core.services.audit_repository import AuditRepository

audit = AuditRepository()


def render_park_sessions():
    st.title("Parked Sessions")
    st.write("Crear y gestionar sesiones en estado 'parked'.")

    st.subheader("Crear nueva sesión parked")

    with st.form("create_session_form"):
        series_id = st.text_input("Series ID")
        product_id = st.text_input("Product ID")
        organization_id = st.text_input("Organization ID")
        capacity = st.number_input("Capacity", min_value=1, step=1)

        submitted = st.form_submit_button("Crear sesión")

        if submitted:
            if not series_id or not product_id or not organization_id:
                st.error("Todos los campos son obligatorios.")
            else:
                session = create_parked_session(
                    series_id=series_id,
                    product_id=product_id,
                    organization_id=organization_id,
                    capacity=capacity,
                )
                st.success(f"Sesión creada: {session['id']}")

    st.subheader("Sesiones parked existentes")

    sessions = get_parked_sessions()
    if not sessions:
        st.info("No hay sesiones parked.")
        return

    for s in sessions:
        st.write(f"📦 Sesión: {s['id']}")
        st.write(f"- Product ID: {s['product_id']}")
        st.write(f"- Organization: {s['organization_id']}")
        st.write(f"- Capacity: {s['capacity']}")
        st.write(f"- Pax Registered: {s['pax_registered']}")
        st.write("---")

        if st.button(f"Activar sesión {s['id']}", key=f"activate_{s['id']}"):
            activate_session(s["id"])
            st.success(f"Sesión activada: {s['id']}")
            audit.log(
                action="SESSION_ACTIVATED_FROM_UI",
                session_id=s["id"],
                user_id=None,
            )
            st.experimental_rerun()
