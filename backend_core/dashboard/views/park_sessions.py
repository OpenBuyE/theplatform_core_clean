import streamlit as st

from backend_core.services.session_repository import session_repository
from backend_core.services.session_engine import session_engine
from backend_core.services.audit_repository import log_event


def render_park_sessions():
    st.title("🅿️ Sesiones en Parque")

    st.markdown(
        """
Estas son las sesiones **parked**, listas para ser activadas por el sistema
o manualmente (debug).
"""
    )

    sessions = session_repository.get_sessions(status="parked", limit=200)

    if not sessions:
        st.info("No hay sesiones parked.")
        return

    for s in sessions:
        with st.expander(f"🅿️ Sesión {s['id']} — Producto {s['product_id']}"):
            st.write("**Estado:**", s["status"])
            st.write("**Aforo:**", f"{s['pax_registered']} / {s['capacity']}")
            st.write("**Sequence:**", s["sequence_number"])
            st.write("**Serie:**", s["series_id"])

            st.markdown("---")

            # Botón para activar esta sesión (debug)
            if st.button("Activar esta sesión", key=f"activate_{s['id']}"):
                activated = session_engine.activate_session(s["id"])

                if activated:
                    st.success(f"Sesión activada: {s['id']}")
                    log_event(
                        action="ui_manual_activation",
                        session_id=s["id"],
                        metadata={}
                    )
                    st.experimental_rerun()
                else:
                    st.error("No se pudo activar la sesión.")

            with st.expander("🔍 Debug info"):
                st.json(s)
