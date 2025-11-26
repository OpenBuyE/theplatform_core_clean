import streamlit as st

# ---------------------------------------------------------
# IMPORTS DEL LAYOUT (MINIMAL, SIN CSS)
# ---------------------------------------------------------
from backend_core.dashboard.ui.layout import (
    setup_page,
    render_header,
    render_sidebar,
)

# ---------------------------------------------------------
# DIAGNÓSTICO DE IMPORTS — PARA RECUPERAR EL MENÚ
# ---------------------------------------------------------

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

    # Importar resto de vistas sin bloquear
    try:
        from backend_core.dashboard.views.park_sessions import render_park_sessions
    except:
        pass

    try:
        from backend_core.dashboard.views.active_sessions import render_active_sessions
    except:
        pass

    try:
        from backend_core.dashboard.views.product_catalog_pro import render_product_catalog_pro
    except:
        pass

    try:
        from backend_core.dashboard.views.product_details_pro import render_product_details_pro
    except:
        pass

    try:
        from backend_core.dashboard.views.product_creator_pro import render_product_creator_pro
    except:
        pass

    try:
        from backend_core.dashboard.views.category_manager_pro import render_category_manager_pro
    except:
        pass

    try:
        from backend_core.dashboard.views.provider_manager_pro import render_provider_manager_pro
    except:
        pass

    try:
        from backend_core.dashboard.views.admin_seeds import render_admin_seeds
    except:
        pass


# ---------------------------------------------------------
# RENDERIZAR UNA PÁGINA SEGÚN SELECCIÓN
# ---------------------------------------------------------

def render_page(page: str):
    """
    Router de páginas. Llama a la vista correspondiente.
    """

    # Importar vistas aquí, no arriba (evita fallos globales)
    from backend_core.dashboard.views.operator_dashboard import render_operator_dashboard
    from backend_core.dashboard.views.operator_dashboard_pro import render_operator_dashboard_pro

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

    # ROUTER
    if page == "Parked Sessions":
        if render_park_sessions: render_park_sessions()
        else: st.error("Error en Parked Sessions")

    elif page == "Active Sessions":
        if render_active_sessions: render_active_sessions()
        else: st.error("Error en Active Sessions")

    elif page == "Operator Dashboard":
        render_operator_dashboard()

    elif page == "Operator Dashboard Pro":
        render_operator_dashboard_pro()

    elif page == "Product Catalog Pro":
        if render_product_catalog_pro: render_product_catalog_pro()
        else: st.error("Error en Product Catalog Pro")

    elif page == "Product Details Pro":
        if render_product_details_pro: render_product_details_pro()
        else: st.error("Error en Product Details Pro")

    elif page == "Product Creator Pro":
        if render_product_creator_pro: render_product_creator_pro()
        else: st.error("Error en Product Creator Pro")

    elif page == "Category Manager Pro":
        if render_category_manager_pro: render_category_manager_pro()
        else: st.error("Error en Category Manager Pro")

    elif page == "Provider Manager Pro":
        if render_provider_manager_pro: render_provider_manager_pro()
        else: st.error("Error en Provider Manager Pro")

    elif page == "Admin Seeds":
        if render_admin_seeds: render_admin_seeds()
        else: st.error("Error en Admin Seeds")

    else:
        st.info("Seleccione una opción del menú.")


# ---------------------------------------------------------
# FUNCIÓN PRINCIPAL — NECESARIA PARA main.py
# ---------------------------------------------------------

def main():
    """Función necesaria para que main.py pueda ejecutar el dashboard."""
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


# ---------------------------------------------------------
# EJECUCIÓN DIRECTA DESDE STREAMLIT
# ---------------------------------------------------------

if __name__ == "__main__":
    main()
