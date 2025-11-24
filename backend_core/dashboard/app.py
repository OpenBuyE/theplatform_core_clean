# backend_core/dashboard/app.py

import streamlit as st

from backend_core.dashboard.views.park_sessions import render_park_sessions
from backend_core.dashboard.views.active_sessions import render_active_sessions
from backend_core.dashboard.views.chains import render_chains
from backend_core.dashboard.views.history_sessions import render_history_sessions
from backend_core.dashboard.views.audit_logs import render_audit_logs
from backend_core.dashboard.views.admin_engine import render_admin_engine
from backend_core.dashboard.views.admin_seeds import render_admin_seeds
from backend_core.dashboard.views.admin_users import render_admin_users
from backend_core.dashboard.views.contract_payment_status import render_contract_payment_status
from backend_core.dashboard.views.admin_operators_kyc import render_admin_operators_kyc
from backend_core.dashboard.views.operator_dashboard import render_operator_dashboard


def main():
    st.set_page_config(page_title="Compra Abierta Dashboard", layout="wide")

    if "page" not in st.session_state:
        st.session_state["page"] = "Parked Sessions"

    st.sidebar.title("Compra Abierta")

    pages = [
        "Parked Sessions",
        "Active Sessions",
        "Chains",
        "History",
        "Audit Logs",
        "Admin Engine",
        "Admin Seeds",
        "Admin Users",
        "Admin Operators / KYC",
        "Operator Dashboard",
        "Contract & Payment Status",
    ]

    page = st.sidebar.radio(
        "Panel",
        pages,
        index=pages.index(st.session_state["page"]),
    )

    st.session_state["page"] = page

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
    elif page == "Admin Users":
        render_admin_users()
    elif page == "Admin Operators / KYC":
        render_admin_operators_kyc()
    elif page == "Operator Dashboard":
        render_operator_dashboard()
    elif page == "Contract & Payment Status":
        render_contract_payment_status()


if __name__ == "__main__":
    main()
