# backend_core/dashboard/views/history_sessions_old.py

import streamlit as st

from backend_core.services import supabase_client


def render_history_sessions():
    st.title("History Sessions")
    st.write("Sesiones finalizadas (finished / expired).")

    resp = (
        supabase_client.table("ca_sessions")
        .select("*")
        .in_("status", ["finished", "expired"])
        .order("finished_at", desc=True)
        .execute()
    )
    sessions = resp.data or []

    if not sessions:
        st.info("No hay sesiones finalizadas.")
        return

    st.json(sessions)
