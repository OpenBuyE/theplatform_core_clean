import streamlit as st

from backend_core.services.session_repository import session_repository
from backend_core.services.session_engine import session_engine
from backend_core.services.audit_repository import log_event


def render_park_sessions():
    st.header("🅿️ Sesiones en Parque")

    # ---------------------------------------------------------
    # Obtener sesiones en estado "parked"
    # ---------------------------------------------------------
    sessions = session_repository.get_sessions(status="parked")

    if not sessions:
        st.info("No hay sesiones parked.")
        return

    # ---------------------------------------------------------
    # Render/expanders de cada sesión
    # ---------------------------------------------------------
    for s in sessions:
        with st.expander(f"🅿️ Sesión {s['id']} — Producto {s['product_id']}"):
            st.write("**Producto:**", s["product_id"])
            st.write("**Organización:**", s["organization_id"])
            st.write("**Serie:**", s["series_id"])
            st.write("**Sequence:**", s["sequence_number"])
            st.write("**Capacidad:**", s["capacity"])
            st.write("**Estado:**", s["status"])
            st.write("**Creada:**", s.get("created_at"))

            st.divider()

            # -------------------------------------------------
            # Botón: ACTIVAR SESIÓN
            # -------------------------------------------------
            if st.button(f"🚀 Activar sesión {s['id']}", key=f"activate_{s['id']}"):
                activated = session_repository.activate_session(s["id"])

                if activated:
                    log_event(
                        action="session_activated_from_panel",
                        session_id=s["id"],
                        metadata={"activated_at": activated.get("activated_at")}
                    )
                    st.success(f"Sesión activada correctamente: {activated['id']}")

                    # 🔁 Reemplazo correcto de experimental_rerun()
                    st.rerun()

                else:
                    st.error("No se pudo activar la sesión.")

            st.divider()
