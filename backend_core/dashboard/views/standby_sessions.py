import streamlit as st

from backend_core.services.acl import require_org, require_permission
from backend_core.services.session_repository import get_standby_sessions


@require_org
@require_permission("session.view")
def render_standby_sessions():
    st.header("🟧 Sesiones en Standby / Coming Soon")

    rows = get_standby_sessions()

    if not rows:
        st.info("No hay sesiones en Standby para esta organización.")
        return

    for row in rows:
        st.subheader(f"🟦 {row.get('series_code','')} — Standby")

        st.write(f"**ID:** {row.get('id')}")
        st.write(f"**Serie:** {row.get('series_id','-')}")
        st.write(f"**Módulo:** {row.get('module_id','-')}")
        st.write(f"**Aforo:** {row.get('max_pax','-')} pax")
        st.write(f"**Umbral de activación:** {row.get('activation_threshold','-')} pax")
        st.write(f"**Publicitable desde:** {row.get('advertise_from','-')}")
        st.write(f"**Estado:** `{row.get('status','-')}`")

        st.markdown("---")
