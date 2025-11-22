# active_sessions.py
# Vista de sesiones activas + añadir participantes test + bloquear aforo

import streamlit as st

from backend_core.services.session_repository import session_repository
from backend_core.services.participant_repository import participant_repository
from backend_core.services.session_engine import session_engine
from backend_core.services.adjudicator_engine import adjudicator_engine
from backend_core.services.audit_repository import log_event


def render_active_sessions():

    st.title("🔵 Active Sessions")

    sessions = session_repository.get_sessions(status="active")

    if not sessions:
        st.info("No hay sesiones activas en este momento.")
        return

    for s in sessions:
        with st.expander(f"🟢 Sesión {s['id']} — Producto {s['product_id']}"):

            st.write("**Estado:**", s["status"])
            st.write("**Aforo:**", f"{s['pax_registered']} / {s['capacity']}")
            st.write("**Serie:**", s["series_id"])
            st.write("**Sequence:**", s["sequence_number"])
            st.write("**Activada:**", s.get("activated_at"))
            st.write("**Expira:**", s.get("expires_at"))

            st.divider()

            # ------------------------------------------------------------
            #  BOTÓN: Añadir participante test (blindado por capacidad)
            # ------------------------------------------------------------
            if st.button(f"Añadir Participante Test → {s['id']}", key=f"add_{s['id']}_test"):
                # 1) Verificar aforo antes de intentar insertar
                if s["pax_registered"] >= s["capacity"]:
                    st.error("❌ Aforo completo. No se pueden añadir más participantes.")
                else:
                    new = participant_repository.add_test_participant(s["id"])

                    if new:
                        log_event(
                            action="test_participant_added",
                            session_id=s["id"],
                            metadata={"participant_id": new["id"]}
                        )
                        st.success(f"👍 Participante TEST añadido: {new['id']}")
                        st.rerun()
                    else:
                        st.error("No se pudo añadir participante test.")

            st.divider()

            # ------------------------------------------------------------
            #  BOTÓN: Forzar adjudicación (TEST manual)
            # ------------------------------------------------------------
            if st.button(f"⚡ Forzar Adjudicación → {s['id']}", key=f"force_adj_{s['id']}"):
                result = adjudicator_engine.adjudicate_session(s["id"])
                if result:
                    st.success(f"🎉 Adjudicatario: {result['id']}")
                else:
                    st.error("No se pudo adjudicar esta sesión.")

            st.divider()

            # ------------------------------------------------------------
            #  Mostrar lista de participantes
            # ------------------------------------------------------------
            parts = participant_repository.get_participants_by_session(s["id"])

            st.write("### Participantes:")
            if not parts:
                st.info("Sin participantes todavía.")
            else:
                for p in parts:
                    st.write(f"- {p['id']} — {'✔️' if p['is_awarded'] else ''}")


