# backend_core/dashboard/app.py

import streamlit as st

# ============================
# IMPORTAR TODAS LAS VISTAS
# ============================

from backend_core.dashboard.views.park_sessions import render_park_sessions
from backend_core.dashboard.views.active_sessions import render_active_sessions
from backend_core.dashboard.views.chains import render_chains
from backend_core.dashboard.views.history_sessions import render_history_sessions
from backend_core.dashboard.views.audit_logs import render_audit_logs

from backend_core.dashboard.views.admin_engine import render_admin_engine
from backend_core.dashboard.views.admin_seeds import render_admin_seeds
from backend_core.dashboard.views.admin_operators_kyc import (
    render_admin_operators_kyc,
)

from backend_core.dashboard.views.operator_dashboard import (
    render_operator_dashboard,
)

from backend_core.dashboard.views.module_inspector import (
    render_module_inspector,
)

from backend_core.dashboard.views.contract_payment_status import (
    render_contract_payment_status,
)

# NUEVO — Catálogo Profesional de productos
from backend_core.dashboard.views.product_catalog_pro import (
    render_product_catalog_pro,
)


# ============================
# CONFIG STREAMLIT
# ============================

st.set_page_config(
    page_title="Platform Core",
    layout="wide",
)


# ============================
# MAIN APP
# ============================

def main():
    st.title("⚡ Platform Core — Admin Panel")

    st.sidebar.title("Navegación")

    page = st.sidebar.selectbox(
        "Selecciona página",
        [
            "Parked Sessions",
            "Active Sessions",
            "Chains",
            "History",
            "Audit Logs",
            "Admin Engine",
            "Admin Seeds",
            "Admin Operators / KYC",
            "Operator Dashboard",
            "Module Inspector",
            "Contract & Payment Status",
            "Products Catalog PRO",
        ],
    )

    # ===== ROUTER =====

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

    elif page == "Admin Operators / KYC":
        render_admin_operators_kyc()

    elif page == "Operator Dashboard":
        render_operator_dashboard()

    elif page == "Module Inspector":
        render_module_inspector()

    elif page == "Contract & Payment Status":
        render_contract_payment_status()

    elif page == "Products Catalog PRO":
        render_product_catalog_pro()


# Entrypoint
if __name__ == "__main__":
    main()
