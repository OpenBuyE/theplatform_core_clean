import streamlit as st

from backend_core.services.acl import require_org, require_permission
from backend_core.services.session_repository import get_active_sessions
from backend_core.services.session_engine import advance_series
from backend_core.services.audit_repository import log_action
from backend_core.services.context import get_current_user


@require_org
@require_permission("session.view")
def render_active_sessions():
    st.header("🔥 Sesiones Activas")

    rows = get_active_sessions()

    if not rows:
        st.info("No hay sesiones activas en esta organización.")
        return

    for r in rows:
        sid = r["id"]
        series_id = r.get("series_id")
        seq = r.get("sequence_number")

        st.subheader(f"🔥 Sesión {sid}")
        st.write(f"**Serie:** {series_id or '-'}")
        st.write(f"**Secuencia:** {seq or '-'}")
        st.write(f"**Estado:** `{r.get('status','')}`")
        st.write(f"**Expira:** {r.get('expires_at','')}")
        st.write(f"**Aforo:** {r.get('current_pax','0')} / {r.get('max_pax','-')} pax")

        colA, colB = st.columns(2)

        with colA:
            if st.button("🛑 Cerrar sesión", key=f"close_{sid}"):
                log_action(
                    action="session_closed_manual",
                    session_id=sid,
                    performed_by=get_current_user(),
                )

                # Cerramos sesión manualmente
                from backend_core.services.supabase_client import update_row
                update_row("sessions", sid, {"status": "finished"})

                st.success("Sesión cerrada.")
                st.experimental_rerun()

        with colB:
            if series_id and st.button("⏭️ Avanzar serie", key=f"advance2_{sid}"):
                advance_series(series_id)
                st.success("Serie avanzada.")
                st.experimental_rerun()

        st.markdown("---")




