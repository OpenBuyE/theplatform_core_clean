import streamlit as st

# ---------------------------
#   LOGIN Y SESIÓN
# ---------------------------
from backend_core.dashboard.views.login import render_login
from backend_core.services.session_manager import is_logged_in, logout

# ---------------------------
#   LAYOUT
# ---------------------------
from backend_core.dashboard.ui.layout import (
    render_app_header,
    render_sidebar,
)

# ---------------------------
#   MOTOR AUTOMÁTICO
# ---------------------------
from backend_core.services.session_engine import process_expired_sessions

# ---------------------------
#   VISTAS
# ---------------------------
from backend_core.dashboard.views.park_sessions import render_park_sessions
from backend_core.dashboard.views.active_sessions import render_active_sessions
from backend_core.dashboard.views.scheduled_sessions import render_scheduled_sessions
from backend_core.dashboard.views.standby_sessions import render_standby_sessions
from backend_core.dashboard.views.chains import render_chains
from backend_core.dashboard.views.audit_logs import render_audit_logs
from backend_core.dashboard.views.admin_users import render_admin_users
from backend_core.dashboard.views.admin_series import render_admin_series
from backend_core.dashboard.views.history_sessions import render_history_sessions


# ============================================================
#                       MAIN APP
# ============================================================

def main():
    st.set_page_config(
        page_title="Compra Abierta – Panel Operativo",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # ---------------------------------------------------------
    # 1) MOTOR AUTOMÁTICO → Revisar expiraciones
    # ---------------------------------------------------------
    process_expired_sessions()

    # ---------------------------------------------------------
    # 2) Si no hay login → mostrar pantalla inicio sesión
    # ---------------------------------------------------------
    if not is_logged_in():
        render_login()
        return

    # ---------------------------------------------------------
    # 3) Header superior
    # ---------------------------------------------------------
    render_app_header()

    # ---------------------------------------------------------
    # 4) Sidebar usuario
    # ---------------------------------------------------------
    st.sidebar.markdown("### 👤 Usuario")

    user_email = st.session_state.get("user_email", "desconocido")
    st.sidebar.info(f"Conectado como:\n**{user_email}**")

    if st.sidebar.button("Cerrar sesión"):
        logout()
        st.experimental_rerun()

    st.sidebar.markdown("---")

    # ---------------------------------------------------------
    # 5) Sidebar organización
    # ---------------------------------------------------------
    render_sidebar()

    # ---------------------------------------------------------
    # 6) Navegación
    # ---------------------------------------------------------
    st.sidebar.title("📊 Navegación")

    page = st.sidebar.selectbox(
        "Selecciona vista",
        [
            "Parque de Sesiones",
            "Sesiones Activas",
            "Sesiones Programadas",
            "Sesiones en Standby",
            "Cadenas Operativas",
            "Histórico de Sesiones",   # ← NUEVA VISTA
            "Auditoría",
            "Series de Sesiones",
            "Gestión de Usuarios",
        ],
    )

    # ---------------------------------------------------------
    # 7) Router de vistas
    # ---------------------------------------------------------
    if page == "Parque de Sesiones":
        render_park_sessions()

    elif page == "Sesiones Activas":
        render_active_sessions()

    elif page == "Sesiones Programadas":
        render_scheduled_sessions()

    elif page == "Sesiones en Standby":
        render_standby_sessions()

    elif page == "Cadenas Operativas":
        render_chains()

    elif page == "Histórico de Sesiones":
        render_history_sessions()

    elif page == "Auditoría":
        render_audit_logs()

    elif page == "Series de Sesiones":
        render_admin_series()

    elif page == "Gestión de Usuarios":
        render_admin_users()


# ============================================================
#                       ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()




