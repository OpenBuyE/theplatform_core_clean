import streamlit as st

from backend_core.services.acl import require_org, require_permission
from backend_core.services.session_repository import get_scheduled_sessions


@require_org
@require_permission("session.view")
def render_scheduled_sessions():
    st.header("🗓 Sesiones Programadas")

    rows = get_scheduled_sessions()

    if not rows:
        st.info("No hay sesiones programadas en esta organización.")
        return

    for row in rows:
        st.subheader(f"📌 {row.get('series_code','')} — Sesión programada")
        st.write(f"**ID:** {row.get('id')}")
        st.write(f"**Serie:** {row.get('series_id','-')}")
        st.write(f"**Módulo:** {row.get('module_id','-')}")
        st.write(f"**Fecha de salida:** {row.get('start_at','-')}")
        st.write(f"**Aforo:** {row.get('max_pax','-')} pax")
        st.write(f"**Umbral de activación:** {row.get('activation_threshold','-')} pax")

        st.write(f"**Estado:** `{row.get('status','-')}`")
        st.markdown("---")
