# backend_core/dashboard/views/active_sessions.py

import streamlit as st

from backend_core.services.session_repository import get_active_sessions
from backend_core.services.participant_repository import (
    add_test_participant,
    get_participants_for_session,
)
from backend_core.services.adjudicator_engine import adjudicator_engine
from backend_core.services.product_repository import get_product
from backend_core.services.module_repository import get_module_for_session


def render_active_sessions():
    st.header("Active Sessions")

    sessions = get_active_sessions()
    if not sessions:
        st.info("No hay sesiones activas.")
        return

    for s in sessions:
        st.write("### Sesión:", s["id"])
        st.write(f"- Estado: {s['status']}")
        st.write(f"- Aforo: {s['pax_registered']} / {s['capacity']}")
        st.write(f"- Activada en: {s.get('activated_at')}")

        # Producto
        product = get_product(s["product_id"])
        if product:
            st.write(f"- Producto: **{product['name']}** — {product['price']}€")

        # Módulo
        module = get_module_for_session(s["id"])
        if module:
            st.write(f"- Módulo: **{module['module_code']}** — {module['id']}")

        st.write("---")

        # Botón: añadir participante test
        if st.button(f"Añadir participante test → sesión {s['id']}"):
            add_test_participant(s["id"])
            st.success("Participante de prueba añadido.")

        # Listar participantes
        participants = get_participants_for_session(s["id"])
        if participants:
            st.write("#### Participantes:")
            for p in participants:
                awarded_flag = " ✅ (adjudicatario)" if p.get("is_awarded") else ""
                st.write(f"- {p['id']} — user: {p['user_id']}{awarded_flag}")
        else:
            st.write("Sin participantes todavía.")

        # Botón: forzar adjudicación
        if st.button(f"Forzar adjudicación → sesión {s['id']}"):
            try:
                result = adjudicator_engine.run_adjudication(s["id"])
                st.success(
                    f"Adjudicación ejecutada. Ganador: {result['winner_participant_id']}"
                )
            except Exception as e:
                st.error(f"Error al adjudicar: {e}")

        st.write("----")
