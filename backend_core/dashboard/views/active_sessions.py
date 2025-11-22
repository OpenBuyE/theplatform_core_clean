import streamlit as st
import pandas as pd

from backend_core.services.session_repository import session_repository
from backend_core.services.participant_repository import participant_repository
from backend_core.services.adjudicator_engine import adjudicator_engine
from backend_core.services.audit_repository import log_event


# ---------------------------------------------------------
#  Vista: Sesiones Activas
# ---------------------------------------------------------
def render_active_sessions():
    st.header("🟢 Sesiones Activas")

    # -----------------------------------------------------
    # Obtener sesiones activas (máximo 200)
    # -----------------------------------------------------
    sessions = session_repository.get_sessions(status="active", limit=200)

    if not sessions:
        st.info("No hay sesiones activas en este momento.")
        return

    # -----------------------------------------------------
    # Mostrar cada sesión activa en un expander
    # -----------------------------------------------------
    for s in sessions:
        with st.expander(f"🟢 Sesión {s['id']} — Producto {s['product_id']}"):
            st.write("**Estado:**", s["status"])
            st.write("**Aforo:**", f"{s['pax_registered']} / {s['capacity']}")
            st.write("**Sequence:**", s["sequence_number"])
            st.write("**Serie:**", s["series_id"])
            st.write("**Activada en:**", s.get("activated_at"))
            st.write("**Expira en:**", s.get("expires_at"))

            st.divider()

            # -------------------------------------------------
            # Participantes de la sesión
            # -------------------------------------------------
            participants = participant_repository.get_participants_by_session(s["id"])
            df = pd.DataFrame(participants)

            if participants:
                st.subheader("👥 Participantes")
                st.dataframe(df)
            else:
                st.warning("Esta sesión no tiene participantes aún.")

            st.divider()

            # -------------------------------------------------
            # BOTÓN 1 — Añadir participante TEST
            # -------------------------------------------------
            st.subheader("➕ Añadir Participante (TEST)")

            col1, col2 = st.columns(2)

            with col1:
                default_price = 10.0
                default_amount = 1.0
                default_qty = 1

                add_btn = st.button(
                    f"Añadir participante TEST a {s['id']}",
                    key=f"addtest_{s['id']}"
                )

            if add_btn:
                new_p = participant_repository.add_participant(
                    session_id=s["id"],
                    user_id="TEST-USER",
                    organization_id=s["organization_id"],
                    amount=default_amount,
                    price=default_price,
                    quantity=default_qty,
                )

                if new_p:
                    log_event(
                        action="test_participant_added",
                        session_id=s["id"],
                        user_id="TEST-USER",
                        metadata={"participant_id": new_p["id"]}
                    )
                    st.success("Participante TEST añadido.")
                    st.rerun()
                else:
                    st.error("Error al añadir participante.")

            st.divider()

            # -------------------------------------------------
            # BOTÓN 2 — Forzar adjudicación manual (TEST)
            # -------------------------------------------------
            st.subheader("🏁 Forzar Adjudicación Manual (TEST)")

            force_btn = st.button(
                f"Forzar adjudicación de la sesión {s['id']}",
                key=f"forceadj_{s['id']}",
                help="Usar solo para pruebas. Ejecuta el motor determinista aunque no haya llegado a aforo."
            )

            if force_btn:
                awarded = adjudicator_engine.adjudicate_session(s["id"])

                if awarded:
                    st.success(
                        f"Adjudicación ejecutada.\n"
                        f"Participante adjudicatario: {awarded['id']}"
                    )
                    st.rerun()
                else:
                    st.error("No fue posible adjudicar la sesión (ver logs).")

    st.info("Fin de la lista de sesiones activas.")
