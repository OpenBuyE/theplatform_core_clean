# backend_core/dashboard/app.py

import streamlit as st

# ================================
# IMPORTAR VISTAS (todas activas)
# ================================
from backend_core.dashboard.views.park_sessions import render_park_sessions
from backend_core.dashboard.views.active_sessions import render_active_sessions
from backend_core.dashboard.views.chains import render_chains
from backend_core.dashboard.views.history_sessions import render_history_sessions
from backend_core.dashboard.views.audit_logs import render_audit_logs

# Admin Engine (opciones del sistema)
from backend_core.dashboard.views.admin_engine import render_admin_engine

# Admin Seeds (semillas del sistema)
from backend_core.dashboard.views.admin_seeds import render_admin_seeds

# Operator dashboards
from backend_core.dashboard.views.operator_dashboard import render_operator_dashboard
from backend_core.dashboard.views.operator_dashboard_pro import render_operator_dashboard_pro

# Product Catalog
from backend_core.dashboard.views.product_catalog_pro import render_product_catalog_pro
from backend_core.dashboard.views.product_details_pro import render_product_details_pro
from backend_core.dashboard.views.product_creator_pro import render_product_creator_pro

# Category Manager
from backend_core.dashboard.views.category_manager_pro import render_category_manager_pro

# Provider Manager
from backend_core.dashboard.views.provider_manager_pro import render_provider_manager_pro

# ================================
# CONFIG GENERAL DE PÁGINA
# ================================
def setup_page():
    st.set_page_config(
        page_title="The Platform — Core",
        page_icon="⚙️",
        layout="wide"
    )

def render_header():
    st.markdown(
        """
        <h1 style="color:#0066CC; font-weight:800; margin-bottom:0;">
            🧠 The Platform — Core Dashboard
        </h1>
        <p style="color:#444; margin-top:4px;">
            Motor operativo profesional · Sistema modular · Compra Abierta 3.0
        </p>
        <hr style="margin-top:10px; margin-bottom:15px;">
        """,
        unsafe_allow_html=True,
    )


# ================================
# MAIN
# ================================
def main():
    setup_page()
    render_header()

    # Sidebar
    with st.sidebar:
        st.title("📌 Navegación")

        page = st.selectbox(
            "Selecciona una vista:",
            [
                "Parked Sessions",
                "Active Sessions",
                "Chains Manager",
                "History Sessions",
                "Audit Logs",
                "Operator Dashboard",
                "Operator Dashboard Pro",
                "Product Catalog Pro",
                "Product Details Pro",
                "Product Creator Pro",
                "Category Manager Pro",
                "Provider Manager Pro",
                "Admin Seeds",
                "Admin Engine",
            ]
        )

        st.markdown("---")
        st.caption("© Compra Abierta / The Platform")

    # ================================
    # SELECTOR DE RUTAS
    # ================================
    if page == "Parked Sessions":
        render_park_sessions()

    elif page == "Active Sessions":
        render_active_sessions()

    elif page == "Chains Manager":
        render_chains()

    elif page == "History Sessions":
        render_history_sessions()

    elif page == "Audit Logs":
        render_audit_logs()

    elif page == "Operator Dashboard":
        render_operator_dashboard()

    elif page == "Operator Dashboard Pro":
        render_operator_dashboard_pro()

    elif page == "Product Catalog Pro":
        render_product_catalog_pro()

    elif page == "Product Details Pro":
        render_product_details_pro()

    elif page == "Product Creator Pro":
        render_product_creator_pro()

    elif page == "Category Manager Pro":
        render_category_manager_pro()

    elif page == "Provider Manager Pro":
        render_provider_manager_pro()

    elif page == "Admin Seeds":
        render_admin_seeds()

    elif page == "Admin Engine":
        render_admin_engine()


# ================================
# ENTRYPOINT
# ================================
if __name__ == "__main__":
    main()
