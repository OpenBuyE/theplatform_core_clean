import streamlit as st

from backend_core.services.session_repository import session_repository
from backend_core.services.session_engine import session_engine
from backend_core.services.audit_repository import log_event


def render_park_sessions():
    st.title("🟦 Sesiones Parked")

    st.markdown("""
Estas son las sesiones en **estado parked**, pendientes de activación.
Una sesión parked puede ser activada manualmente o automáticamente
cuando termina la anterior en su misma serie.
    """)

    st.divider()

    sessions = session_repository.get_parked_sessions(limit=200)

    if not sessions:
        st.info("No hay sesiones parked.")
        return

    for s in sessions:
        with st.expander(f"🟦 Sesión {s['id']} — Producto {s['product_id']}"):

            st.write("**Estado:**", s["status"])
            st.write("**Aforo requerido:**", s["capacity"])
            st.write("**Pax registrados:**", s["pax_registered"])
            st.write("**Serie:**", s["series_id"])
            st.write("**Sequence:**", s["sequence_number"])

            st.markdown("---")

            st.subheader("🚀 Activar sesión manualmente")

            if st.button(f"Activar sesión {s['id']}", key=f"activate_{s['id']}"):
                activated = session_repository.activate_session(s["id"])

                if activated:
                    log_event(
                        action="ui_activate_session",
                        session_id=s["id"],
                        metadata={"activated_session_id": activated["id"]}
                    )
                    st.success(f"Sesión activada: {activated['id']}")
                    st.experimental_rerun()
                else:
                    st.error("No se pudo activar la sesión.")

            st.markdown("---")

            with st.expander("🔍 Debug info"):
                st.json(s)
