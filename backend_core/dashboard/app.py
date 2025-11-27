import streamlit as st

# =========================================================
# IMPORTS DEL LAYOUT MINIMAL
# =========================================================
from backend_core.dashboard.ui.layout import (
    setup_page,
    render_header,
    render_sidebar,
)

# =========================================================
# DIAGNÓSTICO DE IMPORTS
# =========================================================
def diagnostic_imports():
    st.sidebar.markdown("### 🔍 Diagnóstico de imports")

    views = {
        "Operator Login": ("operator_login", "render_operator_login"),
        "Operator Dashboard": ("operator_dashboard", "render_operator_dashboard"),
        "Operator Dashboard Pro": ("operator_dashboard_pro", "render_operator_dashboard_pro"),
        "Operator Manager Pro": ("operator_manager_pro", "render_operator_manager_pro"),
        "Parked Sessions": ("park_sessions", "render_park_sessions"),
        "Active Sessions": ("active_sessions", "render_active_sessions"),
        "Session Chains": ("chains", "render_chains"),
        "Session History": ("history_sessions", "render_history_sessions"),
        "Audit Logs": ("audit_logs", "render_audit_logs"),
        "Product Catalog Pro": ("product_catalog_pro", "render_product_catalog_pro"),
        "Product Details Pro": ("product_details_pro", "render_product_details_pro"),
        "Product Creator Pro": ("product_creator_pro", "render_product_creator_pro"),
        "Category Manager Pro": ("category_manager_pro", "render_category_manager_pro"),
        "Provider Manager Pro": ("provider_manager_pro", "render_provider_manager_pro"),
        "Products Browser": ("products_browser", "render_products_browser"),
        "Engine Monitor": ("engine_monitor", "render_engine_monitor"),
        "Admin Seeds": ("admin_seeds", "render_admin_seeds"),
        "Admin Series": ("admin_series", "render_admin_series"),
        "Admin Users": ("admin_users", "render_admin_users"),
        "Admin Operators KYC": ("admin_operators_kyc", "render_admin_operators_kyc"),
        "Admin Engine": ("admin_engine", "render_admin_engine"),
        "Contract Payment Status": ("contract_payment_status", "render_contract_payment_status"),
        "Operator Debug": ("operator_debug", "render_operator_debug"),
    }

    for label, (module_name, func_name) in views.items():
        try:
            __import__(f"backend_core.dashboard.views.{module_name}", fromlist=[func_name])
            st.sidebar.success(f"{label} import OK")
        except Exception as e:
            st.sidebar.error(f"{label} import FAIL: {e}")


# =========================================================
# ROUTING
# =========================================================
def render_page(page: str):
    def safe_import(module_name, func_name):
        try:
            module = __import__(f"backend_core.dashboard.views.{module_name}", fromlist=[func_name])
            return getattr(module, func_name)
        except Exception:
            return None

    routes = {
        "Operator Login": safe_import("operator_login", "render_operator_login"),
        "Operator Dashboard": safe_import("operator_dashboard", "render_operator_dashboard"),
        "Operator Dashboard Pro": safe_import("operator_dashboard_pro", "render_operator_dashboard_pro"),
        "Operator Manager Pro": safe_import("operator_manager_pro", "render_operator_manager_pro"),
        "Parked Sessions": safe_import("park_sessions", "render_park_sessions"),
        "Active Sessions": safe_import("active_sessions", "render_active_sessions"),
        "Session Chains": safe_import("chains", "render_chains"),
        "Session History": safe_import("history_sessions", "render_history_sessions"),
        "Audit Logs": safe_import("audit_logs", "render_audit_logs"),
        "Product Catalog Pro": safe_import("product_catalog_pro", "render_product_catalog_pro"),
        "Product Details Pro": safe_import("product_details_pro", "render_product_details_pro"),
        "Product Creator Pro": safe_import("product_creator_pro", "render_product_creator_pro"),
        "Category Manager Pro": safe_import("category_manager_pro", "render_category_manager_pro"),
        "Provider Manager Pro": safe_import("provider_manager_pro", "render_provider_manager_pro"),
        "Products Browser": safe_import("products_browser", "render_products_browser"),
        "Engine Monitor": safe_import("engine_monitor", "render_engine_monitor"),
        "Admin Seeds": safe_import("admin_seeds", "render_admin_seeds"),
        "Admin Series": safe_import("admin_series", "render_admin_series"),
        "Admin Users": safe_import("admin_users", "render_admin_users"),
        "Admin Operators KYC": safe_import("admin_operators_kyc", "render_admin_operators_kyc"),
        "Admin Engine": safe_import("admin_engine", "render_admin_engine"),
        "Contract Payment Status": safe_import("contract_payment_status", "render_contract_payment_status"),
        "Operator Debug": safe_import("operator_debug", "render_operator_debug"),
    }

    render_function = routes.get(page)

    if render_function is None:
        st.error(f"La vista '{page}' no está disponible.")
        return

    try:
        if page == "Product Details Pro":
            if "product_details_id" not in st.session_state:
                st.warning("Seleccione un producto en Product Catalog Pro.")
            else:
                render_function(st.session_state["product_details_id"])
        else:
            render_function()
    except Exception as e:
        st.error(f"Error ejecutando la vista '{page}': {e}")


# =========================================================
# MAIN
# =========================================================
def main():
    setup_page()
    render_header()
    render_sidebar()

    diagnostic_imports()

    page = st.sidebar.selectbox(
        "Navigation",
        [
            "Operator Login",
            "Operator Dashboard",
            "Operator Dashboard Pro",
            "Operator Manager Pro",
            "Parked Sessions",
            "Active Sessions",
            "Session Chains",
            "Session History",
            "Audit Logs",
            "Product Catalog Pro",
            "Product Details Pro",
            "Product Creator Pro",
            "Category Manager Pro",
            "Provider Manager Pro",
            "Products Browser",
            "Engine Monitor",
            "Admin Seeds",
            "Admin Series",
            "Admin Users",
            "Admin Operators KYC",
            "Admin Engine",
            "Contract Payment Status",
            "Operator Debug",
        ]
    )

    if page != "Operator Login" and "operator_id" not in st.session_state:
        from backend_core.dashboard.views.operator_login import render_operator_login
        st.warning("Debe iniciar sesión.")
        render_operator_login()
        return

    render_page(page)


# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    main()
