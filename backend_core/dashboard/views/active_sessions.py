"""
active_sessions.py — versión corregida
Totalmente compatible con:
participant_repository.add_test_participant(session_id, organization_id, index)
"""

import streamlit as st

from backend_core.services.session_repository import session_repository
from backend_core.services.participant_repository import participant_repository
from backend_core.services.session_engine import session_engine
from backend_core.services.adjudicator_engine import adjudicator_engine
from backend_core.services.audit_repository import log_event


def render_active_sessions() -> None:
    st.title("🟢 Sesiones Activas")

    st.divider()

    # Obtener sesiones activas
    sessions = session_repository.get_sessions(status="active", limit=200)

    if not sessions:
        st.info("No hay sesiones activas.")
        return

    for s in sessions:
        session_id = s["id"]
        organization_id = s["organization_id"]
        capacity = s.get("capacity", 0)
        pax = s.get("pax_registered", 0)

        header = f"🟢 Sesión {session_id} — Producto {s.get('product_id', 'N/A')}"
        with st.expander(header, expanded=False):

            st.write("**Estado:**", s.get("status"))
            st.write("**Aforo:**", f"{pax} / {capacity}")
            st.write("**Organization ID:**", organization_id)
            st.write("**Serie:**", s.get("series_id"))
            st.write("**Sequence:**", s.get("sequence_number"))

            st.markdown("---")

            # -----------------------------------------------------
            # BOTÓN: Añadir Participante Test
            # -----------------------------------------------------
            st.subheader("👤 Añadir Participante Test (solo pruebas)")

            if st.button(
                f"➕ Añadir participante test a {session_id}",
                key=f"add_part_{session_id}",
            ):
                if pax >= capacity:
                    st.error("❌ Aforo completo. No se pueden añadir más participantes.")
                else:
                    # Índice = pax actual + 1
                    index = pax + 1

                    inserted = participant_repository.add_test_participant(
                        session_id=session_id,
                        organization_id=organization_id,
                        index=index
                    )

                    if inserted:
                        log_event(
                            action="ui_add_test_participant",
                            session_id=session_id,
                            user_id=inserted.get("user_id"),
                            metadata={"participant_id": inserted.get("id")}
                        )
                        st.success(f"✅ Participante añadido: {inserted.get('id')}")
                        st.rerun()
                    else:
                        st.error("⚠️ No se pudo añadir el participante de prueba.")

            st.markdown("---")

            # -----------------------------------------------------
            # BOTÓN: Forzar adjudicación
            # -----------------------------------------------------
            st.subheader("⚡ Forzar Adjudicación (TEST)")

            if st.button(
                f"⚡ Adjudicar sesión {session_id}",
                key=f"force_adj_{session_id}",
            ):
                try:
                    result = adjudicator_engine.adjudicate_session(session_id)
                    if result:
                        st.success(
                            f"🎉 Adjudicatario: participante {result.get('id')} "
                            f"(user_id={result.get('user_id')})"
                        )
                        st.rerun()
                    else:
                        st.warning("⚠️ No se pudo adjudicar la sesión. Revisar logs.")
                except Exception as e:
                    st.error(f"Error al adjudicar: {e}")

            st.markdown("---")

            # -----------------------------------------------------
            # Listado de participantes
            # -----------------------------------------------------
            st.subheader("📋 Participantes en la Sesión")

            try:
                parts = participant_repository.get_participants_by_session(session_id)
            except Exception as e:
                st.error(f"Error al obtener participantes: {e}")
                parts = []

            if not parts:
                st.info("No hay participantes aún.")
            else:
                st.write(f"Total participantes: {len(parts)}")
                st.table([
                    {
                        "participant_id": p.get("id"),
                        "user_id": p.get("user_id"),
                        "organization": p.get("organization_id"),
                        "amount": p.get("amount"),
                        "price": p.get("price"),
                        "is_awarded": p.get("is_awarded"),
                        "awarded_at": p.get("awarded_at"),
                        "created_at": p.get("created_at"),
                    }
                    for p in parts
                ])

            with st.expander("🔍 Sesión RAW"):
                st.json(s)
