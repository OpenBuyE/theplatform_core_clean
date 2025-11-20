import streamlit as st

from backend_core.services.session_repository import session_repository
from backend_core.services.session_engine import session_engine
from backend_core.services.audit_repository import log_event


def render_park_sessions():
    st.title("🟦 Sesiones en Parque (Parked)")

    sessions = session_repository.get_sessions(status="parked", limit=200)

    if not sessions:
        st.info("No hay sesiones parked en este momento.")
        return

    for s in sessions:
        with st.expander(f"🟦 Sesión {s['id']} — Producto {s['product_id']}"):
            st.write("**Estado:**", s["status"])
            st.write("**Aforo:**", f"{s['pax_registered']} / {s['capacity']}")
            st.write("**Serie:**", s["series_id"])
            st.write("**Sequence:**", s["sequence_number"])
            st.write("**Creada en:**", s.get("created_at"))

            st.markdown("---")

            if st.button(
                "Activar sesión ahora",
                key=f"activate_{s['id']}"
            ):
                activated = session_repository.activate_session(session_id=s["id"])
                if activated:
                    st.success("Sesión activada correctamente.")
                    log_event(
                        action="ui_manual_activation",
                        session_id=s["id"]
                    )
                    st.experimental_rerun()
                else:
                    st.error("No se pudo activar la sesión.")
