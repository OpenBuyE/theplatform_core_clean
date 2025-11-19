import streamlit as st

from backend_core.services.session_repository import (
    get_sessions,
    activate_session
)
from backend_core.services.acl import (
    require_org,
    require_permission
)


@require_org
@require_permission("session.view")
def render_park_sessions():

    st.header("🅿️ Parque de Sesiones")

    rows = get_sessions()
    if not rows:
        st.info("No hay sesiones parked para esta organización.")
        return

    for row in rows:
        st.subheader(f"ID: {row['id']}")

        st.write(f"**Operador:** {row.get('operator_code', '-')}")
        st.write(f"**Proveedor:** {row.get('product_id', '-')}")
        st.write(f"**Estado:** `{row.get('status', '-')}`")
        st.write(f"**Importe:** {row.get('amount', 0)} €")

        # Botón de activación con ACL
        @require_permission("session.activate")
        def activate_ui():
            try:
                activate_session(row["id"])
                st.success("Sesión activada correctamente")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error al activar: {str(e)}")

        if st.button("🚀 Activar Sesión", key=f"activate_{row['id']}"):
            activate_ui()

        st.markdown("---")






