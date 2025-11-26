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

    # Operator Dashboard
    try:
        from backend_core.dashboard.views.operator_dashboard import render_operator_dashboard
        st.sidebar.success("Operator Dashboard import OK")
    except Exception as e:
        st.sidebar.error(f"Operator Dashboard import FAIL: {e}")

    # Operator Dashboard Pro
    try:
        from backend_core.dashboard.views.operator_dashboard_pro import render_operator_dashboard_pro
        st.sidebar.success("Operator Dashboard PRO import OK")
    except Exception as e:
        st.sidebar.error(f"Operator Dashboard PRO import FAIL: {e}")

    # Importar resto de vistas sin bloquear ejecución
    for mod, func in [
        ("park_sessions", "render_park_sessions"),
        ("active_sessions", "render_active_sessions"),
        ("product_catalog_pro", "render_product_catalog_pro"),
        ("product_details_pro", "render_product_details_pro"),
        ("product_creator_pro", "render_product_creator_pro"),
        ("category_manager_pro", "render_category_manager_pro"),
        ("provider_manager_pro", "render_provider_manager_pro"),
        ("admin_seeds", "render_admin_seeds"),
    ]:
        try:
            __import__(f"backend_core.dashboard.views.{mod}", fromlist=[func])
        except:
            pass


# =========================================================
# ROUTER PRINCIPAL — LLAMA A VISTAS
# =========================================================
def render_page(page: str):
    """
    Router de páginas. Llama a la vista correspondiente.
    """

    # Importar vistas aquí para evitar que import rotos bloqueen el menú.
    try:
        from backend_core.dashboard.views.operator_dashboard import render_operator_dashboard
    except:
        render_operator_dashboard = None

    try:
        from backend_core.dashboard.views.operator_dashboard_pro import render_operator_dashboard_pro
    except:
        render_operator_dashboard_pro = None

    try:
        from backend_core.dashboard.views.park_sessions import render_park_sessions
    except:
        render_park_sessions = None

    try:
        from backend_core.dashboard.views.active_sessions import render_active_sessions
    except:
        render_active_sessions = None

    try:
        from backend_core.dashboard.views.product_catalog_pro import render_product_catalog_pro
    except:
        render_product_catalog_pro = None

    try:
        from backend_core.dashboard.views.product_details_pro import render_product_details_pro
    except:
        render_product_details_pro = None

    try:
        from backend_core.dashboard.views.product_creator_pro import render_product_creator_pro
    except:
        render_product_creator_pro = None

    try:
        from backend_core.dashboard.views.category_manager_pro import render_category_manager_pro
    except:
        render_category_manager_pro = None

    try:
        from backend_core.dashboard.views.provider_manager_pro import render_provider_manager_pro
    except:
        render_provider_manager_pro = None

    try:
        from backend_core.dashboard.views.admin_seeds import render_admin_seeds
    except:
        render_admin_seeds = None


    # ---------------- ROUTING ----------------

    if page == "Parked Sessions":
        if render_park_sessions:
            try: render_park_sessions()
            except Exception as e: st.error(f"Error en Parked Sessions: {e}")
        else:
            st.error("Parked Sessions no disponible")

    elif page == "Active Sessions":
        if render_active_sessions:
            try: render_active_sessions()
            except Exception as e: st.error(f"Error en Active Sessions: {e}")
        else:
            st.error("Active Sessions no disponible")

    elif page == "Operator Dashboard":
        if render_operator_dashboard:
            try: render_operator_dashboard()
            except Exception as e: st.error(f"Error en Operator Dashboard: {e}")
        else:
            st.error("Operator Dashboard no disponible")

    elif page == "Operator Dashboard Pro":
        if render_operator_dashboard_pro:
            try: render_operator_dashboard_pro()
            except Exception as e: st.error(f"Error en Operator Dashboard PRO: {e}")
        else:
            st.error("Operator Dashboard PRO no disponible")

    elif page == "Product Catalog Pro":
        if render_product_catalog_pro:
            try: render_product_catalog_pro()
            except Exception as e: st.error(f"Error en Product Catalog Pro: {e}")
        else:
            st.error("Product Catalog Pro no disponible")

    elif page == "Product Details Pro":
        if render_product_details_pro:
            try:
                if "product_details_id" not in st.session_state:
                    st.warning("Primero seleccione un producto en el Catálogo.")
                else:
                    render_product_details_pro(st.session_state["product_details_id"])
            except Exception as e:
                st.error(f"Error en Product Details Pro: {e}")
        else:
            st.error("Product Details Pro no disponible")

    elif page == "Product Creator Pro":
        if render_product_creator_pro:
            try: render_product_creator_pro()
            except Exception as e: st.error(f"Error en Product Creator Pro: {e}")
        else:
            st.error("Product Creator Pro no disponible")

    elif page == "Category Manager Pro":
        if render_category_manager_pro:
            try: render_category_manager_pro()
            except Exception as e: st.error(f"Error en Category Manager Pro: {e}")
        else:
            st.error("Category Manager Pro no disponible")

    elif page == "Provider Manager Pro":
        if render_provider_manager_pro:
            try: render_provider_manager_pro()
            except Exception as e: st.error(f"Error en Provider Manager Pro: {e}")
        else:
            st.error("Provider Manager Pro no disponible")

    elif page == "Admin Seeds":
        if render_admin_seeds:
            try: render_admin_seeds()
            except Exception as e: st.error(f"Error en Admin Seeds: {e}")
        else:
            st.error("Admin Seeds no disponible")

    else:
        st.info("Seleccione una opción del menú.")


# =========================================================
# FUNCIÓN QUE main.py NECESITA
# =========================================================
def main():
    setup_page()
    render_header()
    render_sidebar()

    diagnostic_imports()

    page = st.sidebar.selectbox(
        "Navigation",
        [
            "Parked Sessions",
            "Active Sessions",
            "Session Chains",
            "Session History",
            "Audit Logs",
            "Operator Dashboard",
            "Operator Dashboard Pro",
            "Product Catalog Pro",
            "Product Details Pro",
            "Product Creator Pro",
            "Category Manager Pro",
            "Provider Manager Pro",
            "Admin Seeds",
        ]
    )

    render_page(page)


# =========================================================
# EJECUCIÓN DIRECTA
# =========================================================
if __name__ == "__main__":
    main()
