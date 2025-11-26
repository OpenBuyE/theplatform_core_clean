# backend_core/dashboard/views/session_chains.py

import streamlit as st

from backend_core.services.session_repository import (
    get_session_series,
    get_sessions_by_series,
)
from backend_core.services.product_repository_v2 import get_product_v2
from backend_core.services.module_repository import get_module_for_session
from backend_core.services.audit_repository import get_adjudication_log


# ======================================================================
# RENDER PRINCIPAL
# ======================================================================
def render_session_chains():
    st.title("🔗 Session Chains")

    # ---------------------------------------------------------
    # Verificación de login
    # ---------------------------------------------------------
    operator_id = st.session_state.get("operator_id")
    if not operator_id:
        st.error("Debe iniciar sesión como operador.")
        return

    # ---------------------------------------------------------
    # Cargar series disponibles
    # ---------------------------------------------------------
    try:
        series_list = get_session_series(operator_id)
    except Exception as e:
        st.error(f"Error cargando series: {e}")
        return

    if not series_list:
        st.info("No hay cadenas de sesiones registradas.")
        return

    # ---------------------------------------------------------
    # Selección de serie
    # ---------------------------------------------------------
    series_ids = [s["id"] for s in series_list]

    selected_series = st.selectbox(
        "Seleccionar cadena de sesiones",
        options=series_ids
    )

    if not selected_series:
        st.info("Seleccione una cadena.")
        return

    # ---------------------------------------------------------
    # Cargar sesiones de la serie
    # ---------------------------------------------------------
    try:
        sessions = get_sessions_by_series(selected_series, operator_id)
    except Exception as e:
        st.error(f"Error cargando sesiones de la serie: {e}")
        return

    st.markdown(f"## Cadena `{selected_series}`")
    st.markdown("---")

    # ---------------------------------------------------------
    # Mostrar todas las sesiones pertenecientes a la cadena
    # ---------------------------------------------------------
    for s in sessions:
        _render_chain_session_card(s)

        st.markdown("---")


# ======================================================================
# TARJETA DE SESIÓN DENTRO DE UNA CADENA
# ======================================================================
def _render_chain_session_card(s: dict):
    """
    Muestra la información completa de una sesión perteneciente a una serie.
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
    st.write(f"- previous_chain_hash: `{s.get('previous_chain_hash')}`")

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
    # Resultado de adjudicación (si finalizada)
    # ---------------------------------------------------------
    if s.get("status") == "finished":
        st.markdown("#### 🏆 Adjudicación")

        try:
            log = get_adjudication_log(s["id"])
        except:
            log = None

        if log:
            st.write(f"- Ganador: `{log['winner_id']}`")
            st.write(f"- Seed: `{log['seed_input']}`")
            st.write(f"- Hash: `{log['hash_output']}`")
            st.write(f"- Timestamp: `{log['timestamp']}`")
        else:
            st.warning("No hay log de adjudicación para esta sesión.")

    st.markdown("</div>", unsafe_allow_html=True)
