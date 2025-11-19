import streamlit as st

from backend_core.dashboard.views.login import render_login
from backend_core.services.session_manager import is_logged_in, logout

# Componentes UI
from backend_core.dashboard.ui.layout import (
    render_app_header,
    render_sidebar,
)

# Vistas operativas
from backend_core.dashboard.views.park_sessions import render_park_sessions
from backend_core.dashboard.views.active_sessions import render_active_sessions
from backend_core.dashboard.views.chains import render_chains
from backend_core.dashboard.views.audit_logs import render_audit_logs


def main():
    # ---------------------------------------------------
    #   Configuración general de Streamlit
    # ---------------------------------------------------
    st.set_page_config(
        page_title="Compra Abierta – Panel Operativo",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # ---------------------------------------------------
    #   1) Si NO hay login → mostrar pantalla de login
    # ---------------------------------------------------
    if not is_logged_in():
        render_login()
        return

    # ---------------------------------------------------
    #   2) Si hay login → mostrar header + panel operativo
    # ---------------------------------------------------
    render_app_header()

    # -------------- SIDEBAR CON LOGIN -------------------
    st.sidebar.markdown("### 👤 Usuario")

    user_email = st.session_state.get("user_email", "desconocido")
    st.sidebar.info(f"Conectado como:\n**{user_email}**")

    if st.sidebar.button("Cerrar sesión"):
        logout()
        st.experimental_rerun()

    st.sidebar.markdown("---")

    # -------------- SIDEBAR DE ORGANIZACIÓN --------------
    render_sidebar()

    # -------------- MENU PRINCIPAL -----------------------
    st.sidebar.title("📊 Navegación")

    page = st.sidebar.selectbox(
        "Selecciona vista",
        [
            "Parque de Sesiones",
            "Sesiones Activas",
            "Cadenas Operativas",
            "Auditoría",
        ],
    )

    # --------------------------


