# backend_core/dashboard/views/chains.py

import streamlit as st

from backend_core.services import supabase_client


def render_chains():
    st.title("Chains (Series de sesiones)")
    st.write("Visualiza las series de sesiones (rolling) y sus sesiones asociadas.")

    # Cargar series
    series_resp = (
        supabase_client.table("ca_session_series")
        .select("*")
        .order("created_at")
        .execute()
    )
    series_list = series_resp.data or []

    if not series_list:
        st.info("No hay series de sesiones.")
        return

    for series in series_list:
        st.subheader(f"🧬 Serie: {series['id']}")
        st.write(f"- Organization ID: {series['organization_id']}")
        st.write(f"- Product ID: {series['product_id']}")
        st.write(f"- Created at: {series['created_at']}")
        st.write("---")

        # Cargar sesiones de la serie
        sessions_resp = (
            supabase_client.table("ca_sessions")
            .select("*")
            .eq("series_id", series["id"])
            .order("created_at")
            .execute()
        )
        sessions = sessions_resp.data or []

        if sessions:
            st.write("Sesiones de esta serie:")
            st.json(sessions)
        else:
            st.info("No hay sesiones asociadas a esta serie todavía.")

        st.divider()
