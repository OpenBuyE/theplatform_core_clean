import streamlit as st

# ---------------------------------------------------------
# IMPORTS DEL LAYOUT (MINIMAL)
# ---------------------------------------------------------
from backend_core.dashboard.ui.layout import (
    setup_page,
    render_header,
    render_sidebar,
)

# ---------------------------------------------------------
# PRUEBAS DE IMPORT — DIAGNÓSTICO (TEMPORAL)
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
# IMPORTS DEL RESTO DE VISTAS
# (aunque fallen no rompen la app gracias a los try/except)
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
    from backend_cor_
