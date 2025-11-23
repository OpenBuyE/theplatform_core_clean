# backend_core/dashboard/views/audit_logs.py

import streamlit as st

from backend_core.services import supabase_client


def render_audit_logs():
    st.title("Audit Logs")
    st.write("Registros de auditoría desde ca_audit_logs.")

    limit = st.number_input("Número de registros a mostrar", min_value=10, max_value=500, value=100, step=10)

    resp = (
        supabase_client.table("ca_audit_logs")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    logs = resp.data or []

    if not logs:
        st.info("No hay registros de auditoría.")
        return

    st.json(logs)
