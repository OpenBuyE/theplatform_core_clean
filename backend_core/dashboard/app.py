# backend_core/dashboard/app.py

import streamlit as st

# Importación de vistas existentes
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
from backend_core.dashboard.views.module_inspector import (
    render_module_inspector,
)


def main():
    st.set_page_config(
        page_title="Platform Core Dashboard",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.sidebar.title("Platform Core — Safe Boot Mode")

    menu = st.sidebar.selectbox(
        "Navegación",
        [
            "Module Inspector",
            "Parked Sessions",
            "Active Sessions",
            "Chains",
            "History",
            "Audit Logs",
            "Contract & Payment Status",
            "Operator Dashboard",
            # ❌ PRO DASHBOARD REMOVED TEMPORARILY
            # "Operator Dashboard Pro",
            "Admin Engine",
            "Admin Seeds",
            "Admin Operators / KYC",
        ],
    )

    # RENDER DE VISTAS
    if menu == "Parked Sessions":
        render_park_sessions()

    elif menu == "Active Sessions":
        render_active_sessions()

    elif menu == "Chains":
        render_chains()

    elif menu == "History":
        render_history_sessions()

    elif menu == "Audit Logs":
        render_audit_logs()

    elif menu == "Admin Engine":
        render_admin_engine()

    elif menu == "Admin Operators / KYC":
        render_admin_operators_kyc()

    elif menu == "Contract & Payment Status":
        render_contract_payment_status()

    elif menu == "Operator Dashboard":
        render_operator_dashboard()

    elif menu == "Module Inspector":
        render_module_inspector()

    elif menu == "Admin Seeds":
        render_admin_seeds()


if __name__ == "__main__":
    main()
