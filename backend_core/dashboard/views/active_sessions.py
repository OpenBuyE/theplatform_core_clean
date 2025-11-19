import streamlit as st
from backend_core.services.session_repository import get_active_sessions


def render_active_sessions():
    st.header("🔥 Sesiones Activas")

    rows = get_active_sessions()

    if not rows:
        st.info("No hay sesiones activas actualmente.")
        return

    for row in rows:
        st.subheader(f"ID: {row['id']}")
        st.write(f"**Operador:** {row.get('operator_code', '-')}")
        st.write(f"**Proveedor:** {row.get('product_id', '-')}")
        st.write(f"**Estado:** `{row.get('status', '-')}`")
        st.write(f"**Importe:** {row.get('amount', 0)} €")
        st.write(f"**Cadena:** {row.get('chain_group_id', '-')}")
        st.write(f"**Creada:** {row.get('created_at', '-')}")

        st.markdown("---")


