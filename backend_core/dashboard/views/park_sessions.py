import streamlit as st
from backend_core.services.session_repository import get_sessions

def render():
    st.header("🅿️ Parque de Sesiones")

    rows = get_sessions()

    for row in rows:
        st.subheader(f"ID: {row['id']}")
        st.write(f"**Operador:** {row.get('operator_code','-')}")
        st.write(f"**Proveedor:** {row.get('product_id','-')}")
        st.write(f"**Estado:** `{row.get('status','-')}`")
        st.write(f"**Importe:** {row.get('amount',0)} €")
        st.markdown("---")



