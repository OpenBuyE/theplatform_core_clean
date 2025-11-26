# backend_core/dashboard/views/audit_logs.py

import streamlit as st
from datetime import datetime

from backend_core.services.audit_repository import (
    get_all_logs_for_operator,
    get_log_details,
)


# ======================================================================
# RENDER PRINCIPAL
# ======================================================================
def render_audit_logs():
    st.title("🛰 Audit Logs — Sistema")

    # ---------------------------------------------------------
    # Verificación de login
    # ---------------------------------------------------------
    operator_id = st.session_state.get("operator_id")
    if not operator_id:
        st.error("Debe iniciar sesión como operador.")
        return

    # ---------------------------------------------------------
    # Cargar logs del operador (multi-país)
    # ---------------------------------------------------------
    try:
        logs = get_all_logs_for_operator(operator_id)
    except Exception as e:
        st.error(f"Error cargando logs: {e}")
        return

    if not logs:
        st.info("No hay registros de auditoría.")
        return

    # ---------------------------------------------------------
    # Filtro por tipo de evento
    # ---------------------------------------------------------
    event_types = sorted({log["event_type"] for log in logs})
    selected_event = st.selectbox(
        "Filtrar por tipo de evento",
        ["Todos"] + event_types
    )

    if selected_event != "Todos":
        logs = [l for l in logs if l["event_type"] == selected_event]

    st.markdown("---")

    # ---------------------------------------------------------
    # LISTADO DE LOGS
    # ---------------------------------------------------------
    for log in logs:
        _render_log_card(log, operator_id)


# ======================================================================
# TARJETA INDIVIDUAL DE LOG
# ======================================================================
def _render_log_card(log: dict, operator_id: str):
    """
    Muestra un log individual con resumen + botón de detalles.
    """

    event_type = log.get("event_type", "unknown")
    ts = log.get("timestamp")
    session_id = log.get("session_id")
    operator = log.get("operator_id")
    country = log.get("country_code", "N/A")

    # Colores por tipo de evento
    COLOR = {
        "session_created": "#4A90E2",
        "session_activated": "#007AFF",
        "session_finished": "#20B858",
        "session_expired": "#F5A623",
        "session_adjudicated": "#8B5CF6",
        "engine_event": "#50E3C2",
        "login": "#3A3A3A",
        "error": "#D0021B",
    }

    color = COLOR.get(event_type, "#999999")

    st.markdown(
        f"""
        <div style="
            padding: 15px;
            margin: 10px 0;
            background-color: #FFFFFF;
            border-left: 6px solid {color};
            border: 1px solid #E5E5E5;
            border-radius: 8px;
        ">
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"### 🧾 Evento `{event_type}`")

    st.write(f"- **Fecha:** {ts}")
    st.write(f"- **Sesión:** `{session_id}`")
    st.write(f"- **Operador:** `{operator}`")
    st.write(f"- **País:** `{country}`")

    # Botón de detalle
    detail_key = f"detail_{log['id']}"
    if st.button("Ver detalles completos", key=detail_key):
        _render_log_details(log["id"], operator_id)

    st.markdown("</div>", unsafe_allow_html=True)


# ======================================================================
# DETALLE COMPLETO DE LOG
# ======================================================================
def _render_log_details(log_id: str, operator_id: str):

    st.markdown("### 📘 Detalles del Log")

    try:
        details = get_log_details(log_id, operator_id)
    except Exception as e:
        st.error(f"No se pudieron cargar los detalles: {e}")
        return

    if not details:
        st.warning("No hay información adicional en este log.")
        return

    # Renderizado clave-valor
    for key, value in details.items():
        st.write(f"**{key}:** `{value}`")
