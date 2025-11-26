# backend_core/dashboard/views/active_sessions.py

import streamlit as st

from backend_core.services.session_repository import (
    get_active_sessions,
    finish_session,
    get_participants_for_session,
)
from backend_core.services.product_repository_v2 import get_product_v2
from backend_core.services.module_repository import get_module_for_session
from backend_core.services.adjudicator_engine import run_adjudication
from backend_core.services.audit_repository import log_event


# ======================================================================
# RENDER PRINCIPAL
# ======================================================================
def render_active_sessions():
    st.title("🔥 Active Sessions")

    # Operador debe estar logueado
    operator_id = st.session_state.get("operator_id")
    if not operator_id:
        st.error("Debe iniciar sesión como operador.")
        return

    # ---------------------------------------------------------
    # Cargar sesiones activas
    # ---------------------------------------------------------
    try:
        sessions = get_active_sessions(operator_id)
    except Exception as e:
        st.error(f"Error cargando sesiones activas: {e}")
        return

    if not sessions:
        st.info("No hay sesiones activas.")
        return

    # ---------------------------------------------------------
    # LISTA DE SESIONES ACTIVAS
    # ---------------------------------------------------------
    for s in sessions:
        st.markdown(f"## 🔵 Sesión `{s['id']}`")

        st.write(f"- Estado: `{s.get('status')}`")
        st.write(f"- Aforo: {s.get('pax_registered', 0)} / {s.get('aforo', '?')}")
        st.write(f"- Creada en: {s.get('created_at')}")
        st.write(f"- Expira: {s.get('expires_at')}")

        # ---------------------------------------------------------
        # Producto asociado
        # ---------------------------------------------------------
        try:
            product = get_product_v2(s["product_id"])
        except:
            product = None

        if product:
            st.write(f"- Producto: **{product['name']}** — {product['price_final']} €")
            if product.get("image_url"):
                st.image(product["image_url"], width=150)

        # ---------------------------------------------------------
        # Módulo asociado
        # ---------------------------------------------------------
        try:
            module = get_module_for_session(s["id"])
        except:
            module = None

        if module:
            st.write(f"- Módulo asignado: **{module.get('module_code')}**")

        st.markdown("---")

        # ---------------------------------------------------------
        # Participantes
        # ---------------------------------------------------------
        try:
            participants = get_participants_for_session(s["id"])
        except:
            participants = []

        st.subheader("👥 Participantes")
        if participants:
            for p in participants:
                awarded = " 🏆" if p.get("is_awarded") else ""
                st.write(f"- `{p['id']}` — user: {p['user_id']}{awarded}")
        else:
            st.info("Sin participantes todavía.")

        # ---------------------------------------------------------
        # FORZAR ADJUDICACIÓN
        # ---------------------------------------------------------
        if st.button(f"⚡ Ejecutar adjudicación → sesión {s['id']}"):
            try:
                result = run_adjudication(s["id"], operator_id=operator_id)
                winner = result.get("winner_participant_id")

                log_event("session_adjudicated_manual",
                          session_id=s["id"],
                          operator_id=operator_id,
                          winner=winner)

                st.success(f"Adjudicación ejecutada. Ganador: {winner}")

                # Marcar sesión como finalizada
                finish_session(s["id"], operator_id)

                st.experimental_rerun()

            except Exception as e:
                st.error(f"Error ejecutando adjudicación: {e}")

        st.markdown("----")
