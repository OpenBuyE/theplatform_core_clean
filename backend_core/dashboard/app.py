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


# ---------------------------------------------------------
# IMPORTS DEL RESTO DE VISTAS (NO BLOQUEAN EL MENÚ)
# ---------------------------------------------------------

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
# CONFIGURACIÓN BASE
# ---------------------------------------------------------

setup_page()
render_header()
render_sidebar()


# ---------------------------------------------------------
# MENÚ COMPLETO
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# ROUTER — LLAMADA A LAS VISTAS
# ---------------------------------------------------------

if page == "Parked Sessions":
    try:
        render_park_sessions()
    except Exception as e:
        st.error(f"Error en Parked Sessions: {e}")

elif page == "Active Sessions":
    try:
        render_active_sessions()
    except Exception as e:
        st.error(f"Error en Active Sessions: {e}")

elif page == "Operator Dashboard":
    try:
        render_operator_dashboard()
    except Exception as e:
        st.error(f"Error en Operator Dashboard: {e}")

elif page == "Operator Dashboard Pro":
    try:
        render_operator_dashboard_pro()
    except Exception as e:
        st.error(f"Error en Operator Dashboard PRO: {e}")

elif page == "Product Catalog Pro":
    try:
        render_product_catalog_pro()
    except Exception as e:
        st.error(f"Error en Product Catalog Pro: {e}")

elif page == "Product Details Pro":
    try:
        render_product_details_pro()
    except Exception as e:
        st.error(f"Error en Product Details Pro: {e}")

elif page == "Product Creator Pro":
    try:
        render_product_creator_pro()
    except Exception as e:
        st.error(f"Error en Product Creator Pro: {e}")

elif page == "Category Manager Pro":
    try:
        render_category_manager_pro()
    except Exception as e:
        st.error(f"Error en Category Manager Pro: {e}")

elif page == "Provider Manager Pro":
    try:
        render_provider_manager_pro()
    except Exception as e:
        st.error(f"Error en Provider Manager Pro: {e}")

elif page == "Admin Seeds":
    try:
        render_admin_seeds()
    except Exception as e:
        st.error(f"Error en Admin Seeds: {e}")

else:
    st.info("Seleccione una opción del menú.")
