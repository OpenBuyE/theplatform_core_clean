# backend_core/dashboard/app.py
# =====================================================================
# STREAMLIT DASHBOARD — PLATFORM CORE CLEAN
# Estilo Fintech Blanco/Azul + Navegación Completa
# =====================================================================

import streamlit as st
from datetime import datetime

# ============================================
# IMPORTAR TODAS LAS VISTAS
# ============================================

# Sesiones
from backend_core.dashboard.views.park_sessions import render_park_sessions
from backend_core.dashboard.views.active_sessions import render_active_sessions
from backend_core.dashboard.views.chains import render_chains
from backend_core.dashboard.views.history_sessions import render_history_sessions

# Auditoría
from backend_core.dashboard.views.audit_logs import render_audit_logs

# Seeds
from backend_core.dashboard.views.admin_engine import render_admin_engine
from backend_core.dashboard.views.admin_seeds import render_admin_seeds
from backend_core.dashboard.views.admin_operators_kyc import render_admin_operators_kyc

# Operator Dashboards
from backend_core.dashboard.views.operator_dashboard import render_operator_dashboard
from backend_core.dashboard.views.operator_dashboard_pro import render_operator_dashboard_pro

# Módulos
from backend_core.dashboard.views.module_inspector import render_module_inspector

# Productos
from backend_core.dashboard.views.product_catalog_pro import render_product_catalog_pro
from backend_core.dashboard.views.product_details_pro import render_product_details_pro
from backend_core.dashboard.views.product_creator_pro import render_product_creator_pro

# Categorías
from backend
