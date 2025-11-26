# backend_core/dashboard/views/history_sessions.py

import streamlit as st
from datetime import datetime

from backend_core.services.session_repository import (
    get_finished_sessions,
    get_expired_sessions,
)
from backend_core.services.product_repository_v2 import get_product_v2
from backend_core.services.module_repository import get_module_for_session
from backend_core.services.audit_repository import get_adjudication_log


# ======================================================================
# RENDER PRINCIPAL
# ======================================================================
def render_history_sessions():
    st.title("📜 Session History")

    # ---------------------------------------------------------
    # Verificación de login
    # ---------------------------------------------------------
    operator_id = st.session_state.get("operator_id")
    if not operator_id:
        st.error("Debe iniciar sesión como operador.")
        return

    # ---------------------------------------------------------
    # Tabs
    # ---------------------------------------------------------
    tab_finished, tab_expired = st.tabs(["✔ Finalizadas", "⏳ Expiradas"])

    # =========================================================
    # SESIONES FINALIZADAS
    # =========================================================
    with tab_finished:
        st.subheader("✔ Sesiones Finalizadas")

        try:
            sessions = get_finished_sessions(operator_id)
        except Exception as e:
            st.error(f"Error cargando sesiones finalizadas: {e}")
            return

        if not sessions:
            st.info("No hay sesiones finalizadas.")
        else:
            for s in sessions:
                _render_session_card(s, finished=True)

    # =========================================================
    # SESIONES EXPIRADAS
    # =========================================================
    with tab_expired:
        st.subheader("⏳ Sesiones Expiradas")

        try:
            sessions = get_expired_sessions(operator_id)
        except Exception as e:
            st.error(f"Error cargando sesiones expiradas: {e}")
            return

        if not sessions:
            st.info("No hay sesiones expiradas.")
        else:
            for s in sessions:
                _render_session_card(s, finished=False)


# ======================================================================
# RENDER DE TARJETA DE SESIÓN
# ======================================================================
def _render_session_card(s: dict, finished: bool):
    """
    Muestra una tarjeta completa de información de una sesión.
    """

    st.markdown(
        """
        <div style="
            padding: 15px;
            margin: 10px 0;
            background-color: #FFFFFF;
            border: 1px solid #E5E5E5;
            border-radius: 8px;
        ">
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"### 🔹 Sesión `{s['id']}`")

    st.write(f"- Estado: `{s.get('status')}`")
    st.write(f"- Aforo: {s.get('pax_registered', 0)} / {s.get('aforo')}")
    st.write(f"- Creada en: {s.get('created_at')}")
    st.write(f"- Expira: {s.get('expires_at')}")

    # ---------------------------------------------------------
    # Producto asociado
    # ---------------------------------------------------------
    product = None
    try:
        product = get_product_v2(s["product_id"])
    except:
        pass

    if product:
        st.write(
            f"- Producto: **{product['name']}** — {product['price_final']} €"
        )
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
        st.write(f"- Módulo: **{module.get('module_code')}**")

    # ---------------------------------------------------------
    # Log de adjudicación (si acabada)
    # ---------------------------------------------------------
    if finished:
        st.markdown("#### 🏆 Resultado de Adjudicación")

        try:
            log = get_adjudication_log(s["id"])
        except:
            log = None

        if not log:
            st.warning("No hay registro de adjudicación.")
        else:
            st.write(f"- Ganador: `{log.get('winner_id')}`")
            st.write(f"- Seed usada: `{log.get('seed_input')}`")
            st.write(f"- Hash resultante: `{log.get('hash_output')}`")
            st.write(f"- Timestamp: `{log.get('timestamp')}`")

    st.markdown("</div>", unsafe_allow_html=True)
