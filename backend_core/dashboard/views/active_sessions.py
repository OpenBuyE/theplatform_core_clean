import streamlit as st
from backend_core.services.session_repository import session_repository
from backend_core.services.participant_repository import participant_repository
from backend_core.services.adjudicator_engine import adjudicator_engine
from backend_core.services.audit_repository import log_event

def render_active_sessions():
    st.header("🟢 Sesiones Activas")

    sessions = session_repository.get_sessions(status="active", limit=50)

    if not sessions:
        st.info("No hay sesiones activas.")
        return

    for s in sessions:
        with st.expander(f"Sesión {s['id']} — Producto {s['product_id']}"):
            st.write("**Estado:**", s["status"])
            st.write("**Aforo:**", f"{s['pax_registered']} / {s['capacity']}")
            st.write("**Serie:**", s["series_id"])
            st.write("**Sequence:**", s["sequence_number"])
            st.write("**Activada en:**", s.get("activated_at"))
            st.write("**Expira en:**", s.get("expires_at"))

            st.divider()

            # Mostrar participantes actuales
            participants = participant_repository.get_participants_by_session(s["id"])
            st.subheader("Participantes Registrados")
            st.write(participants)

            st.divider()

            # Botón para añadir participante de test
            if s["pax_registered"] < s["capacity"]:
                if st.button("➕ Añadir Participante Test", key=f"add_{s['id']}"):
                    participant_repository.add_participant(
                        session_id=s["id"],
                        user_id="TEST-USER",
                        organization_id=s["organization_id"],
                        amount=10,
                        price=0,
                        quantity=1,
                    )
                    st.success("Participante añadido.")
                    st.rerun()
            else:
                st.warning("Aforo completo. No se pueden añadir más participantes.")

            # Si aforo completo → permitir adjudicar manualmente (TEST)
            if s["pax_registered"] == s["capacity"]:
                if st.button("⚡ Forzar Adjudicación", key=f"force_{s['id']}"):
                    awarded = adjudicator_engine.adjudicate_session(s["id"])
                    if awarded:
                        st.success(f"Adjudicación completada. Participante: {awarded['user_id']}")
                    else:
                        st.error("Error adjudicando la sesión.")
                    st.rerun()
