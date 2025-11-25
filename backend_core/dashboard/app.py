# backend_core/dashboard/app.py

import streamlit as st
from urllib.parse import urlparse, parse_qs

# ============================
# IMPORT VISTAS BASE
# ============================

from backend_core.dashboard.views.park_sessions import render_park_sessions
from backend_core.dashboard.views.active_sessions import render_active_sessions
from backend_core.dashboard.views.chains import render_chains
from backend_core.dashboard.views.history_sessions import render_history_sessions
from backend_core.dashboard.views.audit_logs import render_audit_logs
from backend_core.dashboard.views.operator_dashboard import render_operator_dashboard

# ============================
# IMPORT VISTAS PRO
# ============================

from backend_core.dashboard.views.operator_dashboard_pro import (
    render_operator_dashboard_pro,
)

from backend_core.dashboard.views.product_catalog_pro import (
    render_product_catalog_pro,
)

from backend_core.dashboard.views.product_details_pro import (
    render_product_details_pro,
)

from backend_core.dashboard.views.product_creator_pro import (
    render_product_creator_pro,
)

from backend_core.dashboard.views.category_manager_pro import (
    render_category_manager_pro,
)

from backend_core.dashboard.views.admin_seeds import (
    render_admin_seeds,
)

# ============================
# PAGE CONFIG
# ============================

st.set_page_config(
    page_title="The Platform Core Dashboard",
    page_icon="🧬",
    layout="wide"
)


# ============================
# ROUTER — QUERY PARAMS
# ============================

def detect_product_details_route():
    """Detecta si hay ?product_id=XYZ en la URL para abrir Product Details Pro automáticamente."""
    query = st.experimental_get_query_params()
    if "product_id" in query:
        return query["product_id"][0]
    return None


# ============================
# MAIN
# ============================

def main():

    # ============
    # SIDEBAR NAV
    # ============

    st.sidebar.title("📊 Navigation")

    pages = [
        "Parked Sessions",
        "Active Sessions",
        "Chains",
        "History",
        "Audit Logs",
        "Operator Dashboard",
        "Operator Dashboard Pro",
        "Product Catalog Pro",
        "Product Creator Pro",
        "Category Manager Pro",
        "Admin Seeds",
    ]

    page = st.sidebar.selectbox("Select page", pages)

    st.sidebar.markdown("---")
    st.sidebar.caption("The Platform Core — SaaS Engine")

    # =======================================
    # AUTO-ROUTER: Product Details Pro direct
    # =======================================

    product_id = detect_product_details_route()
    if product_id:
        st.sidebar.success(f"Viewing product: {product_id}")
        return render_product_details_pro(product_id)

    # ============================
    # RENDER PAGES
    # ============================

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

    elif page == "Operator Dashboard":
        render_operator_dashboard()

    elif page == "Operator Dashboard Pro":
        render_operator_dashboard_pro()

    elif page == "Product Catalog Pro":
        render_product_catalog_pro()

    elif page == "Product Creator Pro":
        render_product_creator_pro()

    elif page == "Category Manager Pro":
        render_category_manager_pro()

    elif page == "Admin Seeds":
        render_admin_seeds()


if __name__ == "__main__":
    main()
