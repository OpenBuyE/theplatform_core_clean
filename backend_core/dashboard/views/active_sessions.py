# backend_core/dashboard/views/active_sessions.py

import streamlit as st

from backend_core.services.session_repository import (
    get_active_sessions,
)
from backend_core.services.participant_repository import (
    add_test_participant,
    get_participants_for_session,
)
from backend_core.services.adjudicator_engine import adjudicator_engine
from backend_core.services.product_repository import get_product
from backend_core.services.module_repository import get_module_for_session


# =======================================================
# ACTIVE SESSIONS VIEW
# =======================================================

def render_active_sessions():
    st.header("Active Sessions")

    sessions = get_active_sessions()

    if not sessions:
        st.info("No active sessions.")
        return

    for s in sessions:
        st.write("### Session:", s["id"])
        st.write(f"- Status: {s['status']}")
        st.write(f"- Pax Registered: {s['pax_registered']} / {s['capacity']}")
        st.write(f"- Activated At: {s['activated_at']}")

        # Show product info
        prod = get_product(s["product_id"])
        if prod:
            st.write(f"- Product: **{prod['name']}** — {prod['price']}€")

        # Show module info
        module = get_module_for_session(s["id"])
        if module:
            st.write(f"- Module: **{module['module_code']}** — {module['id']}")

        st.write("----")

        # Add test participant (debug only)
        if st.button(f"Añadir participante test → sesión {s['id']}"):
            add_test_participant(s["id"])
            st.success("Test participant added.")

        # List participants
        participants = get_participants_for_session(s["id"])
        if participants:
            st.write("#### Participants:")
            for p in participants:
                st.write(f"- {p['id']} — {p['amount']}€")

        # Force adjudication
        if st.button(f"Forzar adjudicación → sesión {s['id']}"):
            adjudicator_engine.run_adjudication(s["id"])
            st.success("Adjudication executed.")

        st.write("---")
