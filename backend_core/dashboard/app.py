import streamlit as st

# =========================================================
# IMPORTS DEL LAYOUT MINIMAL (SIN CSS)
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
        "Parked Sessions": ("park_sessions", "render_park_sessions"),
        "Active Sessions": ("active_sessions", "render_active_sessions"),
        "Product Catalog Pro": ("product_catalog_pro", "render_product_catalog_pro"),
        "Product Details Pro": ("product_details_pro", "render_product_details_pro"),
        "Product Creator Pro": ("product_creator_pro", "render_product_creator_pro"),
        "Category Manager Pro": ("category_manager_pro", "render_category_manager_pro"),
        "Provider Manager Pro": ("provider_manager_pro", "render_provider_manager_pro"),
        "Admin Seeds": ("admin_seeds", "render_admin_seeds"),
        "Operator Manager Pro": ("operator_manager_pro", "render_operator_manager_pro"),
    }

    for label, (module_name, func_name) in views.items():
        try:
            __import__(f"backend_core.dashboard.views.{module_name}", fromlist=[func_name])
            st.sidebar.success(f"{label} import OK")
        except Exception as e:
            st.sidebar.error(f"{label} import FAIL: {e}")


# =========================================================
# ROUTER PRINCIPAL — LLAMA A VISTAS
# =========================================================
def render_page(page: str):
    """
    Router estable. Si una vista falla al importar o ejecutar,
    la app NO se cae.
    """

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
        "Parked Sessions": safe_import("park_sessions", "render_park_sessions"),
        "Active Sessions": safe_import("active_sessions", "render_active_sessions"),
        "Product Catalog Pro": safe_import("product_catalog_pro", "render_product_catalog_pro"),
        "Product Details Pro": safe_import("product_details_pro", "render_product_details_pro"),
        "Product Creator Pro": safe_import("product_creator_pro", "render_product_creator_pro"),
        "Category Manager Pro": safe_import("category_manager_pro", "render_category_manager_pro"),
        "Provider Manager Pro": safe_import("provider_manager_pro", "render_provider_manager_pro"),
        "Admin Seeds": safe_import("admin_seeds", "render_admin_seeds"),
        "Operator Manager Pro": safe_import("operator_manager_pro", "render_operator_manager_pro"),
        # Futuro: Session Chains, Session History, Audit Logs...
    }

    render_function = routes.get(page)

    if render_function is None:
        st.error(f"La vista '{page}' no está disponible.")
        return

    # Render seguro
    try:
        # PRODUCT DETAILS PRO REQUIERE product_id
        if page == "Product Details Pro":
            if "product_details_id" not in st.session_state:
                st.warning("Seleccione un producto en Product Catalog Pro.")
            else:
                render_function(st.session_state["product_details_id"])
        else:
            render_function()

    except TypeError as e:
        st.error(f"Error de argumentos en la vista '{page}': {e}")

    except Exception as e:
        st.error(f"Error ejecutando la vista '{page}': {e}")


# =========================================================
# FUNCIÓN PRINCIPAL QUE main.py NECESITA
# =========================================================
def main():
    setup_page()
    render_header()
    render_sidebar()

    diagnostic_imports()

    # MENU PRINCIPAL
    page = st.sidebar.selectbox(
        "Navigation",
        [
            "Operator Login",        # LOGIN DEL OPERADOR
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
            "Admin Seeds",
        ]
    )

    # -----------------------------------------------------
    # PROTECCIÓN BÁSICA: REQUIERE LOGIN PARA CASI TODO
    # -----------------------------------------------------
    if page != "Operator Login" and "operator_id" not in st.session_state:
        st.warning("🔐 Debe iniciar sesión en 'Operator Login' para acceder al panel.")
        # Llamamos directamente al login para comodidad
        try:
            from backend_core.dashboard.views.operator_login import render_operator_login
            render_operator_login()
        except Exception as e:
            st.error(f"No se pudo cargar la pantalla de login: {e}")
        return

    render_page(page)


# =========================================================
# EJECUCIÓN DIRECTA
# =========================================================
if __name__ == "__main__":
    main()
