import streamlit as st
import uuid
from datetime import datetime

from backend_core.services.session_repository import session_repository
from backend_core.services.participant_repository import participant_repository
from backend_core.services.session_engine import session_engine
from backend_core.services.adjudicator_engine import adjudicator_engine
from backend_core.services.audit_repository import log_event


def render_active_sessions():
    st.header("🟢 Sesiones Activas")

    # ---------------------------------------------------------
    # Obtener sesiones activas
    # ---------------------------------------------------------
    sessions = session_repository.get_sessions(status="active", limit=50)

    if not sessions:
        st.info("No hay sesiones activas en este momento.")
        return

    for s in sessions:
        with st.expander(
            f"🟢 Sesión {s['id']} — Serie {s['series_id']} — #{s['sequence_number']}"
        ):
            st.write("**Producto:**", s["product_id"])
            st.write("**Estado:**", s["status"])
            st.write("**Aforo:**", f"{s['pax_registered']} / {s['capacity']}")
            st.write("**Activada en:**", s.get("activated_at"))
            st.write("**Expira en:**", s.get("expires_at"))
            st.write("---")

            # ---------------------------------------------------------
            # BOTÓN: Ver participantes
            # ---------------------------------------------------------
            if st.button(f"Mostrar participantes — {s['id']}"):
                participants = participant_repository.get_participants_by_session(s["id"])
                if participants:
                    st.write(participants)
                else:
                    st.info("No hay participantes en esta sesión.")

            # ---------------------------------------------------------
            # BOTÓN: Añadir participante de prueba
            # ---------------------------------------------------------
            if st.button(f"➕ Añadir Participante Test — {s['id']}"):
                fake_id = str(uuid.uuid4())

                participant_repository.add_participant(
                    session_id=s["id"],
                    user_id=f"test-user-{fake_id}",
                    organization_id=s["organization_id"],
                    amount=1.00,
                    price=1.00,
                    quantity=1,
                )

                log_event(
                    action="test_participant_added",
                    session_id=s["id"],
                    metadata={"fake_id": fake_id},
                )

                st.success("Participante de prueba añadido.")
                st.rerun()

            # ---------------------------------------------------------
            # BOTÓN: Forzar adjudicación manual
            # ---------------------------------------------------------
            if st.button(f"🎯 Forzar adjudicación — {s['id']}"):
                result = adjudicator_engine.adjudicate_session(s["id"])
                if result:
                    st.success(
                        f"Sesión adjudicada. Participante: {result['user_id']}"
                    )
                else:
                    st.error("No se pudo adjudicar la sesión (ver auditoría).")

                st.rerun()

            # ---------------------------------------------------------
            # BOTÓN: Finalizar sesión manualmente
            # ---------------------------------------------------------
            if st.button(f"⛔ Finalizar sesión — {s['id']}"):
                now_iso = datetime.utcnow().isoformat()
                session_repository.mark_session_as_finished(s["id"], now_iso)

                log_event(
                    action="session_marked_finished_manual",
                    session_id=s["id"],
                    metadata={"finished_at": now_iso},
                )

                st.success("Sesión finalizada manualmente.")
                st.rerun()
