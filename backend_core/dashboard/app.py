# backend_core/dashboard/app.py
import streamlit as st

# =============================
#   IMPORTACIÓN DE VISTAS
# =============================

from backend_core.dashboard.views.park_sessions import render_park_sessions
from backend_core.dashboard.views.active_sessions import render_active_sessions
from backend_core.dashboard.views.chains import render_chains
from backend_core.dashboard.views.history_sessions import render_history_sessions
from backend_core.dashboard.views.audit_logs import render_audit_logs
from backend_core.dashboard.views.admin_engine import render_admin_engine
from backend_core.dashboard.views.admin_seeds import render_admin_seeds
from backend_core.dashboard.views.admin_operators_kyc import render_admin_operators_kyc

# PRODUCTOS (PRO)
from backend_core.dashboard.views.product_catalog_pro import render_product_catalog_pro
from backend_core.dashboard.views.product_creator_pro import render_product_creator_pro
from backend_core.dashboard.views.product_details_pro import render_product_details_pro
from backend_core.dashboard.views.category_manager_pro import render_category_manager_pro
from backend_core.dashboard.views.provider_manager_pro import render_provider_manager_pro


# =============================
#   CONFIGURACIÓN STREAMLIT
# =============================
def setup_page():
    st.set_page_config(
        page_title="Platform Core Dashboard",
        page_icon="🧩",
        layout="wide",
    )


# Sidebar limpio para evitar errores
def render_sidebar():
    with st.sidebar:
        st.title("🧭 Panel de Control")

        MENU = [
            "Parked Sessions",
            "Active Sessions",
            "Chains",
            "History",
            "Audit Logs",
            "Admin Engine",
            "Admin Seeds",
            "Operators KYC",
            "Product Catalog Pro",
            "Product Creator Pro",
            "Product Details Pro",
            "Category Manager Pro",
            "Provider Manager Pro",
        ]

        return st.selectbox("Navegación", MENU)


# =============================
#   MAIN ROUTER
# =============================
def main():
    setup_page()
    page = render_sidebar()

    if page == "Parked Sessions":
        render_park_sessions()

    elif page == "Active Sessions":
        render_active_sessions()

    elif page == "Chains":
        render_chains()

    elif page == "History":
        render_history_sessions()

    elif page == "Audit Logs":
        render_audit_logs()

    elif page == "Admin Engine":
        render_admin_engine()

    elif page == "Admin Seeds":
        render_admin_seeds()

    elif page == "Operators KYC":
        render_admin_operators_kyc()

    # ==================================
    #         PRODUCTOS PRO
    # ==================================
    elif page == "Product Catalog Pro":
        render_product_catalog_pro()

    elif page == "Product Creator Pro":
        render_product_creator_pro()

    elif page == "Product Details Pro":
        render_product_details_pro()

    elif page == "Category Manager Pro":
        render_category_manager_pro()

    elif page == "Provider Manager Pro":
        render_provider_manager_pro()


# =============================
#   EJECUCIÓN
# =============================
if __name__ == "__main__":
    main()

