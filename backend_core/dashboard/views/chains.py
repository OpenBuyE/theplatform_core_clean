import streamlit as st
from backend_core.services.session_repository import get_chains


def render_chains():
    st.header("⛓ Cadenas operativas")

    rows = get_chains()

    if not rows:
        st.info("No hay cadenas registradas.")
        return

    for row in rows:
        st.subheader(f"Session ID: {row['id']}")
        st.write(f"Chain group: {row.get('chain_group_id', '-')}")
        st.write(f"Chain index: {row.get('chain_index', '-')}")
        st.write(f"Estado: `{row.get('status', '-')}`")
        st.markdown("---")

