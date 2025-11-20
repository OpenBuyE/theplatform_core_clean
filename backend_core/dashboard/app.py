"""
app.py
Panel Streamlit del backend Compra Abierta (The Platform Core Clean)

Vistas disponibles:
- Parked Sessions
- Active Sessions
- Session Chains
- History
- Audit Logs
- Admin Users
- Admin Seeds
- Admin Engine   ← NUEVO PANEL DE MOTOR

Este archivo gestiona:
- El enrutado del sidebar
- La carga modular de cada vista
- La estructura global del panel
"""

import streamlit as st

# Importación de vistas existentes
from backend_core.dashboard.views.park_sessions import render_park_sessions
from backend_core.dashboard.views.active_sessions import render_active_sessions
from backend_core.dashboard.views.chains import render_chains
from backend_core.dashboard.views.audit_logs import render_audit_logs
from backend_core.dashboard.views.history_sessions import render_history
from backend_core.dashboard.views.admin_users import render_admin_users

# Nuevas vistas
from backend_core.dashboard.views.admin_seeds import render_admin_seeds
from backend_core.dashboard.views.admin_engine import render_admin_engine


# ---------------------------------------------------------
# Configuración general de página
# ---------------------------------------------------------
st.set_page_config(
    page_title="Compra Abierta — Backend Panel",
    page_icon="🟩",
    layout="wide",
)


# ---------------------------------------------------------
# Sidebar (Navegación / Menú principal)
# ---------------------------------------------------------
def render_sidebar():
    st.sidebar.title("📊 Panel Operativo — Compra Abierta")

    selected = st.sidebar.radio(
        "Navegación",
        options=[
            "Parked Sessions",
            "Active Sessions",
            "Chains",
            "History",
            "Audit Logs",
            "Admin Users",
            "Admin Seeds",
            "Admin Engine",   # ← NUEVO
        ],
        index=1,
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("The Platform Core Clean — Deterministic Engine")

    return selected


# ---------------------------------------------------------
# Renderizado principal
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

    elif view == "Admin Seeds":
        render_admin_seeds()

    elif view == "Admin Engine":
        render_admin_engine()

    else:
        st.error("Vista no reconocida.")


if __name__ == "__main__":
    main()

