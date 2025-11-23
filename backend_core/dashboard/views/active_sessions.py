import streamlit as st

from backend_core.services.session_repository import session_repository
from backend_core.services.participant_repository import participant_repository
from backend_core.services.session_engine import session_engine
from backend_core.services.adjudicator_engine import adjudicator_engine
from backend_core.services.audit_repository import log_event


def render_active_sessions() -> None:
    st.title("🟢 Sesiones Activas")

    st.divider()

    sessions = session_repository.get_sessions(status="active", limit=200)

    if not sessions:
        st.info("No hay sesiones activas en este momento.")
        return

    for s in sessions:
        session_id = s["id"]
        capacity = s.get("capacity", 0) or 0
        pax = s.get("pax_registered", 0) or 0

        with st.expander(f"🟢 Sesión {session_id}", expanded=False):

            st.write("**Estado:**", s.get("status"))
            st.write("**Aforo:**", f"{pax} / {capacity}")
            st.write("**Serie:**", s.get("series_id"))
            st.write("**Sequence:**", s.get("sequence_number"))
            st.write("**Activada en:**", s.get("activated_at"))
            st.write("**Expira en:**", s.get("expires_at"))

            st.markdown("---")

            # ================================
            # Añadir participante test
            # ================================
            if pax >= capacity:
                st.error("❌ Aforo completo. No se pueden añadir más participantes.")
            else:
                if st.button(f"➕ Añadir participante test ({session_id})",
                             key=f"add_{session_id}"):
                    new = participant_repository.add_test_participant(s)

                    if new:
                        log_event(
                            action="ui_add_test_participant",
                            session_id=session_id,
                            user_id=new.get("user_id"),
                            metadata={"participant_id": new.get("id")}
                        )
                        st.success(f"🟢 Test participant añadido: {new.get('id')}")
                        st.rerun()
                    else:
                        st.error("Error al añadir participante.")

            st.markdown("---")

            # ================================
            # Forzar Adjudicación
            # ================================
            if st.button(f"⚡ Forzar adjudicación ({session_id})",
                         key=f"force_{session_id}"):
                result = adjudicator_engine.adjudicate_session(session_id)
                if result:
                    st.success(f"🎉 Adjudicatario: {result.get('user_id')}")
                    st.rerun()
                else:
                    st.error("No se pudo adjudicar. Ver auditoría.")

            st.markdown("---")

            # ================================
            # Participantes
            # ================================
            parts = participant_repository.get_participants_by_session(session_id)

            st.subheader("📋 Participantes")

            if not parts:
                st.info("No hay participantes.")
            else:
                st.table([
                    {
                        "id": p.get("id"),
                        "user_id": p.get("user_id"),
                        "amount": p.get("amount"),
                        "is_awarded": p.get("is_awarded"),
                        "created_at": p.get("created_at"),
                    }
                    for p in parts
                ])
