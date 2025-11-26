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
# DEFINICIÓN DE RUTAS (LABEL → módulo + función)
# =========================================================

ROUTE_DEFS = {
    # Login / Identidad
    "Operator Login": ("operator_login", "render_operator_login"),

    # Dashboards
    "Operator Dashboard": ("operator_dashboard", "render_operator_dashboard"),
    "Operator Dashboard Pro": ("operator_dashboard_pro", "render_operator_dashboard_pro"),

    # Gestión de operadores
    "Operator Manager Pro": ("operator_manager_pro", "render_operator_manager_pro"),

    # Sesiones
    "Parked Sessions": ("park_sessions", "render_park_sessions"),
    "Scheduled Sessions": ("scheduled_sessions", "render_scheduled_sessions"),
    "Standby Sessions": ("standby_sessions", "render_standby_sessions"),
    "Active Sessions": ("active_sessions", "render_active_sessions"),
    "Session Chains": ("chains", "render_session_chains"),
    "Session History": ("history_sessions", "render_history_sessions"),

    # Productos / Catálogo
    "Product Catalog Pro": ("product_catalog_pro", "render_product_catalog_pro"),
    "Product Details Pro": ("product_details_pro", "render_product_details_pro"),
    "Product Creator Pro": ("product_creator_pro", "render_product_creator_pro"),
    "Category Manager Pro": ("category_manager_pro", "render_category_manager_pro"),
    "Provider Manager Pro": ("provider_manager_pro", "render_provider_manager_pro"),
    "Products Browser": ("products_browser", "render_products_browser"),

    # Auditoría / Motor / Inspectores
    "Engine Monitor": ("engine_monitor", "render_engine_monitor"),
    "Audit Logs": ("audit_logs", "render_audit_logs"),
    "Module Inspector": ("module_inspector", "render_module_inspector"),
    "Contract Payment Status": ("contract_payment_status", "render_contract_payment_status"),

    # Admin / Backoffice avanzado
    "Admin Seeds": ("admin_seeds", "render_admin_seeds"),
    "Admin Series": ("admin_series", "render_admin_series"),
    "Admin Users": ("admin_users", "render_admin_users"),
    "Admin Operators KYC": ("admin_operators_kyc", "render_admin_operators_kyc"),
    "Admin Engine": ("admin_engine", "render_admin_engine"),
}


# =========================================================
# HELPERS DE ROL Y MENÚ DINÁMICO
# =========================================================

def get_current_role() -> str:
    """
    Devuelve el rol actual del operador, o 'anonymous' si no hay login.
    """
    return st.session_state.get("role", "anonymous")


def get_pages_for_role(role: str):
    """
    Devuelve la lista de labels de menú visibles para un rol dado.
    """
    # Bloques base
    base_sessions = [
        "Parked Sessions",
        "Scheduled Sessions",
        "Standby Sessions",
        "Active Sessions",
        "Session Chains",
        "Session History",
    ]

    base_products = [
        "Product Catalog Pro",
        "Product Details Pro",
        "Product Creator Pro",
        "Category Manager Pro",
        "Provider Manager Pro",
        "Products Browser",
    ]

    base_dashboards = [
        "Operator Dashboard",
        "Operator Dashboard Pro",
    ]

    engine_views = [
        "Engine Monitor",
        "Module Inspector",
        "Contract Payment Status",
    ]

    audit_views = [
        "Audit Logs",
    ]

    admin_views = [
        "Admin Seeds",
        "Admin Series",
        "Admin Users",
        "Admin Operators KYC",
        "Admin Engine",
        "Operator Manager Pro",
    ]

    # Siempre disponible en la parte superior
    login_page = ["Operator Login"]

    # Normalizamos rol
    role = (role or "anonymous").lower()

    if role == "god":
        pages = login_page + base_dashboards + base_sessions + base_products + engine_views + audit_views + admin_views

    elif role == "admin_master":
        pages = login_page + base_dashboards + base_sessions + base_products + engine_views + audit_views + admin_views

    elif role == "supervisor":
        # Asimilamos supervisor ↔ country_admin
        pages = login_page + base_dashboards + base_sessions + base_products + engine_views + audit_views + [
            "Operator Manager Pro",
        ]

    elif role == "auditor":
        pages = login_page + [
            "Session History",
            "Session Chains",
            "Engine Monitor",
            "Audit Logs",
        ]

    elif role == "operator":
        pages = login_page + base_dashboards + [
            "Parked Sessions",
            "Active Sessions",
            "Session History",
            "Product Catalog Pro",
            "Product Details Pro",
            "Product Creator Pro",
            "Category Manager Pro",
            "Provider Manager Pro",
        ]

    else:
        # anonymous o rol desconocido
        pages = login_page

    # Filtramos por rutas realmente definidas
    pages = [p for p in pages if p in ROUTE_DEFS]
    return pages


# =========================================================
# DIAGNÓSTICO DE IMPORTS
# =========================================================
def diagnostic_imports():
    st.sidebar.markdown("### 🔍 Diagnóstico de imports")

    for label, (module_name, func_name) in ROUTE_DEFS.items():
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

    if page not in ROUTE_DEFS:
        st.error(f"La vista '{page}' no está registrada en ROUTE_DEFS.")
        return

    module_name, func_name = ROUTE_DEFS[page]
    render_function = safe_import(module_name, func_name)

    if render_function is None:
        st.error(f"La vista '{page}' no está disponible (import fallido).")
        return

    # Render seguro
    try:
        # Product Details Pro requiere product_id desde session_state
        if page == "Product Details Pro":
            if "product_details_id" not in st.session_state:
                st.warning("Seleccione un producto en Product Catalog Pro para ver detalles.")
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

    # Rol actual (si no hay login → 'anonymous')
    role = get_current_role()

    # Páginas visibles según rol
    pages = get_pages_for_role(role)

    # MENU PRINCIPAL
    page = st.sidebar.selectbox(
        "Navigation",
        pages,
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
