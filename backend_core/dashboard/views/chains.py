import streamlit as st
from backend_core.services.session_repository import get_chains


def render_chains():
    st.header("🔗 Cadenas Operativas")

    rows = get_chains()

    if not rows:
        st.info("No hay sesiones con cadena asignada.")
        return

    for row in rows:
        st.subheader(f"ID: {row['id']}")
        st.write(f"**Operador:** {row.get('operator_code', '-')}")
        st.write(f"**Proveedor:** {row.get('product_id', '-')}")
        st.write(f"**Estado:** `{row.get('status', '-')}`")
        st.write(f"**Importe:** {row.get('amount', 0)} €")
        st.write(f"**Chain Group:** `{row.get('chain_group_id', '-')}`")
        st.write(f"**Creada:** {row.get('created_at', '-')}")
        st.write(f"**Actualizada:** {row.get('updated_at', '-')}")
        
        st.markdown("---")

