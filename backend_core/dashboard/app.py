"""
app.py
Panel Streamlit del backend Compra Abierta (The Platform Core Clean)

Vistas disponibles:
- Parked Sessions       (park_sessions)
- Active Sessions       (active_sessions)
- Session Chains        (chains)
- History               (history_sessions)
- Audit Logs            (audit_logs)
- Admin Users           (admin_users)
- Admin Seeds           (admin_seeds)  ← NUEVA

Este archivo gestiona:
- El enrutado del sidebar
- La carga de cada vista
- La estructura base del panel
"""

import streamlit as st

# Importación de vistas
from backend_core.dashboard.views.park_sessions import render_park_sessions
from backend_core.dashboard.views.active_sessions import render_active_sessions
from backend_core.dashboard.views.chains import render_chains
from backend_core.dashboard.views.audit_logs import render_audit_logs
from backend_core.dashboard.views.history_sessions import render_history
from backend_core.dashboard.views.admin_users import render_admin_users

# NUEVA VISTA
from backend_core.dashboard.views.admin_seeds import render_admin_seeds


# ---------------------------------------------------------
# Configuración general de la página
# ---------------------------------------------------------
st.set_page_config(
    page_title="Compra Abierta — Backend Panel",
    page_icon="🟩",
    layout="wide",
)


# ---------------------------------------------------------
# Sidebar (menú de navegación)
# ---------------------------------------------------------
def render_sidebar():
    st.sidebar.title("📊 Panel Operativo")

    selected = st.sidebar.radio(
        "Navegación",
        options=[
            "Parked Sessions",
            "Active Sessions",
            "Chains",
            "History",
            "Audit Logs",
            "Admin Users",
            "Admin Seeds",        # NUEVA ENTRADA
        ],
        index=1,
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("Compra Abierta — The Platform Core Clean")

    return selected


# ---------------------------------------------------------
# Render principal
# ---------------------------------------------------------
def main():
    view = render_sidebar()

    if view == "Parked Sessions":
        render_park_sessions()

    elif view == "Active Sessions":
        render_active_sessions()

    elif view == "Chains":
        render_chains()

    elif view == "History":
        render_history()

    elif view == "Audit Logs":
        render_audit_logs()

    elif view == "Admin Users":
        render_admin_users()

    elif view == "Admin Seeds":      # NUEVO ENRUTADO
        render_admin_seeds()

    else:
        st.error("Vista no encontrada.")


if __name__ == "__main__":
    main()


