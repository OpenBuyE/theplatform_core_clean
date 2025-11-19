import streamlit as st

from backend_core.dashboard.ui.layout import (
    render_app_header,
    render_sidebar
)

# Vistas
from backend_core.dashboard.views.park_sessions import render_park_sessions
from backend_core.dashboard.views.active_sessions import render_active_sessions
from backend_core.dashboard.views.chains import render_chains
from backend_core.dashboard.views.audit_logs import render_audit_logs


def main():
    # ---- Configuración general ----
    st.set_page_config(
        page_title="Compra Abierta – Panel Operativo",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # ---- Encabezado superior ----
    render_app_header()

    # ---- Sidebar (menú) ----
    st.sidebar.title("📊 Panel Operativo")

    page = st.sidebar.selectbox(
        "Selecciona vista",
        [
            "Parque de Sesiones",
            "Sesiones Activas",
            "Cadenas Operativas",
            "Auditoría"
        ],
    )

    st.sidebar.markdown("---")
    render_sidebar()

    # ---- Router de vistas ----
    if page == "Parque de Sesiones":
        render_park_sessions()

    elif page == "Sesiones Activas":
        render_active_sessions()

    elif page == "Cadenas Operativas":
        render_chains()

    elif page == "Auditoría":
        render_audit_logs()


# Punto de entrada
if __name__ == "__main__":
    main()



