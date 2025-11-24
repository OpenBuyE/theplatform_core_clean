# backend_core/dashboard/app.py

import streamlit as st

# =============================
# Importación de vistas
# =============================

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
from backend_core.dashboard.views.contract_payment_status import (
    render_contract_payment_status,
)
from backend_core.dashboard.views.operator_dashboard import (
    render_operator_dashboard,
)
from backend_core.dashboard.views.operator_dashboard_pro import (
    render_operator_dashboard_pro,
)
from backend_core.dashboard.views.module_inspector import (
    render_module_inspector,
)


# =============================
# Configuración global
# =============================

st.set_page_config(
    page_title="Platform Core Dashboard",
    page_icon="🧩",
    layout="wide",
)


# =============================
# Main
# =============================

def main():

    st.title("🧩 Platform Core — Dashboard")

    # -----------------------------------------
    #   NAVEGACIÓN PRINCIPAL
    # -----------------------------------------
    menu = [
        "Parked Sessions",
        "Active Sessions",
        "Chains",
        "History",
        "Audit Logs",
        "Contract & Payment Status",
        "Operator Dashboard",
        "Operator Dashboard Pro",        # <<< ACTIVADO
        "Module Inspector",
        "Admin Engine",
        "Admin Seeds",
        "Admin Operators / KYC",
    ]

    page = st.sidebar.selectbox("Navigation", menu)

    # -----------------------------------------
    #   RENDER DE VISTAS
    # -----------------------------------------

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

    elif page == "Contract & Payment Status":
        render_contract_payment_status()

    elif page == "Operator Dashboard":
        render_operator_dashboard()

    elif page == "Operator Dashboard Pro":
        render_operator_dashboard_pro()   # <<< YA ESTÁ HABILITADO

    elif page == "Module Inspector":
        render_module_inspector()

    elif page == "Admin Engine":
        render_admin_engine()

    elif page == "Admin Seeds":
        render_admin_seeds()

    elif page == "Admin Operators / KYC":
        render_admin_operators_kyc()


if __name__ == "__main__":
    main()
