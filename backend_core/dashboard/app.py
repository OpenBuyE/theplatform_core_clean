# backend_core/dashboard/app.py
# =====================================================================
# STREAMLIT DASHBOARD — PLATFORM CORE CLEAN
# Estilo Fintech Blanco/Azul + Navegación Completa
# =====================================================================

import streamlit as st
from datetime import datetime

# ============================================
# IMPORTAR TODAS LAS VISTAS
# ============================================

# Sesiones
from backend_core.dashboard.views.park_sessions import render_park_sessions
from backend_core.dashboard.views.active_sessions import render_active_sessions
from backend_core.dashboard.views.chains import render_chains
from backend_core.dashboard.views.history_sessions import render_history_sessions

# Auditoría
from backend_core.dashboard.views.audit_logs import render_audit_logs

# Seeds / Admin
from backend_core.dashboard.views.admin_engine import render_admin_engine
from backend_core.dashboard.views.admin_seeds import render_admin_seeds
from backend_core.dashboard.views.admin_operators_kyc import render_admin_operators_kyc

# Operator Dashboards
from backend_core.dashboard.views.operator_dashboard import render_operator_dashboard
from backend_core.dashboard.views.operator_dashboard_pro import render_operator_dashboard_pro

# Módulos
from backend_core.dashboard.views.module_inspector import render_module_inspector

# Productos
from backend_core.dashboard.views.product_catalog_pro import render_product_catalog_pro
from backend_core.dashboard.views.product_details_pro import render_product_details_pro
from backend_core.dashboard.views.product_creator_pro import render_product_creator_pro

# Categorías
from backend_core.dashboard.views.category_manager_pro import render_category_manager_pro

# Proveedores
from backend_core.dashboard.views.provider_manager_pro import render_provider_manager_pro


# =====================================================================
# CONFIGURACIÓN GLOBAL DEL DASHBOARD
# =====================================================================

st.set_page_config(
    page_title="Platform Core — Dashboard",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo corporativo blanco + azul fintech
CUSTOM_STYLE = """
<style>
/* Fondo general */
body, .stApp {
    background-color: #ffffff !important;
}

/* Tarjetas y contenedores */
.block-container {
    padding-top: 2rem;
}

div[data-testid="stMetricValue"] {
    color: #0057D9 !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #F7F9FC !important;
}

header {
    background: #ffffff00;
}
</style>
"""
st.markdown(CUSTOM_STYLE, unsafe_allow_html=True)


# =====================================================================
# MENÚ LATERAL
# =====================================================================

MENU = [
    "Parked Sessions",
    "Active Sessions",
    "History",
    "Chains",
    "Module Inspector",

    "--- Productos ---",
    "Product Catalog Pro",
    "Product Details Pro",
    "Product Creator Pro",
    "Category Manager Pro",
    "Provider Manager Pro",

    "--- Operador ---",
    "Operator Dashboard",
    "Operator Dashboard Pro",

    "--- Auditoría ---",
    "Audit Logs",

    "--- Administración ---",
    "Admin Seeds",
    "Admin Operators / KYC",
    "Admin Engine",
]

st.sidebar.title("Platform Core Navigation")
page = st.sidebar.selectbox("Navegación", MENU)


# =====================================================================
# RENDER PRINCIPAL SEGÚN LA PÁGINA
# =====================================================================

def main():

    # -------------------------------------
    # SESIONES
    # -------------------------------------
    if page == "Parked Sessions":
        render_park_sessions()

    elif page == "Active Sessions":
        render_active_sessions()

    elif page == "History":
        render_history_sessions()

    elif page == "Chains":
        render_chains()

    # -------------------------------------
    # MÓDULOS
    # -------------------------------------
    elif page == "Module Inspector":
        render_module_inspector()

    # -------------------------------------
    # PRODUCTOS
    # -------------------------------------
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

    # -------------------------------------
    # OPERADOR
    # -------------------------------------
    elif page == "Operator Dashboard":
        render_operator_dashboard()

    elif page == "Operator Dashboard Pro":
        render_operator_dashboard_pro()

    # -------------------------------------
    # AUDITORÍA
    # -------------------------------------
    elif page == "Audit Logs":
        render_audit_logs()

    # -------------------------------------
    # ADMIN
    # -------------------------------------
    elif page == "Admin Seeds":
        render_admin_seeds()

    elif page == "Admin Operators / KYC":
        render_admin_operators_kyc()

    elif page == "Admin Engine":
        render_admin_engine()

    # -------------------------------------
    # DEFAULT / SAFE MODE
    # -------------------------------------
    else:
        st.error("Página no encontrada. Safe Boot Mode activo.")
        st.write(page)


# =====================================================================
# EJECUCIÓN
# =====================================================================
if __name__ == "__main__":
    main()
