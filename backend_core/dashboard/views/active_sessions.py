import streamlit as st
from datetime import datetime

from backend_core.services.session_repository import session_repository
from backend_core.services.participant_repository import participant_repository
from backend_core.services.session_engine import session_engine
from backend_core.services.adjudicator_engine import adjudicator_engine
from backend_core.services.audit_repository import log_event


def render_active_sessions():
    st.header("🟢 Active Sessions")

    # Obtener sesiones activas
    sessions = session_repository.get_sessions(status="active", limit=200)

    if not sessions:
        st.info("No hay sesiones activas.")
        return

    for session in sessions:
        sid = session["id"]
        pax = session.get("pax_registered", 0)
        cap = session.get("capacity", 0)

        with st.expander(f"🟢 Sesión {sid} — {pax}/{cap} participantes"):

            st.write("**Producto:**", session["product_id"])
            st.write("**Organización:**", session["organization_id"])
            st.write("**Serie:**", session["series_id"])
            st.write("**Sequence:**", session["sequence_number"])
            st.write("**Aforo:**", f"{pax}/{cap}")
            st.write("---")

            # -----------------------------------------------------
            # BOTÓN: Añadir PARTICIPANTE TEST sin sobrepasar aforo
            # -----------------------------------------------------
            st.subheader("➕ Añadir Participante Test")

            if pax >= cap:
                st.warning("⚠️ Aforo completo. No se pueden añadir más participantes.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    user_id = st.text_input(f"User ID (test) for {sid}", value="USER-TEST-1")
                with col2:
                    amount = st.number_input(f"Importe aportado", min_value=0.0, value=1.0)

                if st.button(f"Añadir participante → {sid}"):
                    result = participant_repository.add_participant(
                        session_id=sid,
                        user_id=user_id,
                        organization_id=session["organization_id"],
                        amount=amount,
                        price=0,
                        quantity=1,
                    )

                    if result:
                        st.success("Participante añadido.")
                        st.rerun()
                    else:
                        st.error("No se pudo añadir participante.")

            st.write("---")

            # -----------------------------------------------------
            # BOTÓN: FORZAR ADJUDICACIÓN
            # -----------------------------------------------------
            if st.button(f"⚡ Forzar adjudicación {sid}"):
                awarded = adjudicator_engine.adjudicate_session(sid)
                if awarded:
                    st.success(f"Adjudicatario: {awarded['user_id']}")
                else:
                    st.error("No se pudo adjudicar la sesión.")
                st.rerun()
