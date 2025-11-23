"""
active_sessions.py
Vista de sesiones activas — integrada con el motor determinista y el entorno de tests.

Funcionalidades:
- Listar sesiones activas (ca_sessions.status = 'active')
- Mostrar aforo, estado y metadatos
- Botón "Añadir Participante Test" (solo para pruebas internas)
- Bloqueo estricto de aforo: no permite superar capacity
- Botón "Forzar Adjudicación" que llama al adjudicator_engine
- Listado de participantes de la sesión
"""

import streamlit as st

from backend_core.services.session_repository import session_repository
from backend_core.services.participant_repository import participant_repository
from backend_core.services.session_engine import session_engine
from backend_core.services.adjudicator_engine import adjudicator_engine
from backend_core.services.audit_repository import log_event


def render_active_sessions() -> None:
    st.title("🟢 Sesiones Activas")

    st.markdown(
        """
Esta sección muestra todas las **sesiones activas** (`ca_sessions.status = 'active'`).

Una sesión activa:

- Tiene un `capacity` fijo (aforo obligatorio 100%).
- Va incrementando `pax_registered` con cada participante.
- En cuanto se completa el aforo, el motor determinista **adjudica** y la sesión pasa a `finished`.
- Si no completa aforo en 5 días, el motor de expiración la marca `finished` sin adjudicación.
        """
    )

    st.divider()

    # ---------------------------------------------------------
    # Obtener sesiones activas desde el repositorio
    # ---------------------------------------------------------
    sessions = session_repository.get_sessions(status="active", limit=200)

    if not sessions:
        st.info("No hay sesiones activas en este momento.")
        return

    # ---------------------------------------------------------
    # Recorrer cada sesión activa
    # ---------------------------------------------------------
    for s in sessions:
        session_id = s["id"]
        capacity = s.get("capacity", 0) or 0
        pax = s.get("pax_registered", 0) or 0

        header = f"🟢 Sesión {session_id} — Producto {s.get('product_id', 'N/A')}"
        with st.expander(header, expanded=False):

            # Datos básicos de la sesión
            st.write("**Estado:**", s.get("status"))
            st.write("**Aforo:**", f"{pax} / {capacity}")
            st.write("**Organization ID:**", s.get("organization_id"))
            st.write("**Serie:**", s.get("series_id"))
            st.write("**Sequence:**", s.get("sequence_number"))
            st.write("**Activada en:**", s.get("activated_at"))
            st.write("**Expira en:**", s.get("expires_at"))

            st.markdown("---")

            # =================================================
            # BOTÓN: Añadir Participante Test (solo entorno dev)
            # =================================================
            st.subheader("👤 Añadir Participante Test (solo pruebas)")

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    f"➕ Añadir participante test a {session_id}",
                    key=f"add_part_{session_id}",
                ):
                    # Releer valores por seguridad
                    current_pax = s.get("pax_registered", 0) or 0
                    max_pax = s.get("capacity", 0) or 0

                    if current_pax >= max_pax:
                        st.error("❌ Aforo completo. No se pueden añadir más participantes.")
                    else:
                        # IMPORTANTE: aquí pasamos el dict completo de sesión,
                        # no solo el ID, para evitar el TypeError anterior.
                        new = participant_repository.add_test_participant(s)

                        if new:
                            log_event(
                                action="ui_add_test_participant",
                                session_id=session_id,
                                user_id=new.get("user_id"),
                                metadata={"participant_id": new.get("id")}
                            )
                            st.success(f"✅ Participante test añadido: {new.get('id')}")
                            st.rerun()
                        else:
                            st.error("No se pudo añadir el participante de prueba.")

            with col2:
                # =================================================
                # BOTÓN: Forzar adjudicación (TEST manual)
                # =================================================
                st.markdown("### ⚡ Forzar Adjudicación (TEST)")

                if st.button(
                    f"⚡ Forzar Adjudicación → {session_id}",
                    key=f"force_adj_{session_id}",
                ):
                    try:
                        result = adjudicator_engine.adjudicate_session(session_id)
                        if result:
                            st.success(
                                f"🎉 Adjudicatario: participante {result.get('id')} "
                                f"(user_id={result.get('user_id')})"
                            )
                            log_event(
                                action="ui_force_adjudication",
                                session_id=session_id,
                                user_id=result.get("user_id"),
                                metadata={"participant_id": result.get("id")}
                            )
                            st.rerun()
                        else:
                            st.warning("No se pudo adjudicar la sesión (ver logs de auditoría).")
                    except Exception as e:
                        st.error(f"Error al forzar adjudicación: {e}")

            st.markdown("---")

            # =================================================
            # PARTICIPANTES DE LA SESIÓN
            # =================================================
            st.subheader("📋 Participantes de la sesión")

            try:
                parts = participant_repository.get_participants_by_session(session_id)
            except Exception as e:
                st.error(f"Error al obtener participantes: {e}")
                parts = []

            if not parts:
                st.info("No hay participantes registrados en esta sesión.")
            else:
                st.write(f"Total participantes: {len(parts)}")
                # Mostrar una tabla simple
                st.table(
                    [
                        {
                            "participant_id": p.get("id"),
                            "user_id": p.get("user_id"),
                            "amount": p.get("amount"),
                            "quantity": p.get("quantity"),
                            "price": p.get("price"),
                            "is_awarded": p.get("is_awarded"),
                            "awarded_at": p.get("awarded_at"),
                            "created_at": p.get("created_at"),
                        }
                        for p in parts
                    ]
                )

            # =================================================
            # DEBUG opcional
            # =================================================
            with st.expander("🔍 Debug: sesión cruda"):
                st.json(s)

