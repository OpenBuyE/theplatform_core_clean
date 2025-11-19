import streamlit as st

from backend_core.services.session_repository import get_chains
from backend_core.services.acl import (
    require_org,
    require_permission
)


@require_org
@require_permission("chain.view")
def render_chains():

    st.header("🔗 Cadenas Operativas")

    rows = get_chains()
    if not rows:
        st.info("No hay cadenas operativas para esta organización.")
        return

    for row in rows:

        st.subheader(f"ID: {row['id']}")

        st.write(f"**Operador:** {row.get('operator_code', '-')}")
        st.write(f"**Proveedor:** {row.get('product_id', '-')}")
        st.write(f"**Grupo Cadena:** {row.get('chain_group_id', '-')}")
        st.write(f"**Estado:** `{row.get('status', '-')}`")
        st.write(f"**Importe:** {row.get('amount', 0)} €")

        st.markdown("---")


