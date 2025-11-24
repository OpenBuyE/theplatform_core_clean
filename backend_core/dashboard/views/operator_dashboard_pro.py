import streamlit as st
from datetime import datetime

from backend_core.services.supabase_client import table
from backend_core.services.product_repository import get_product
from backend_core.services.module_repository import get_module_for_session
from backend_core.services.session_repository import (
    get_active_sessions,
    get_parked_sessions,
)
from backend_core.services.contract_engine import contract_engine


# ================================
#   DISEÑO ESTILO FINTECH (AZUL)
# ================================
PRIMARY_BLUE = "#2563eb"
LIGHT_BG = "#f8fafc"
SOFT_BORDER = "#e2e8f0"


def _kpi_card(title: str, value: str):
    """Componente estilizado de KPI tipo Revolut/MangoPay"""
    st.markdown(
        f"""
        <div style="
            padding:16px;
            background:white;
            border-radius:10px;
            border:1px solid {SOFT_BORDER};
            box-shadow:0 1px 3px rgba(0,0,0,0.05);
        ">
            <div style="font-size:14px;color:#64748b;">{title}</div>
            <div style="font-size:24px;font-weight:600;color:{PRIMARY_BLUE};">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _session_row(s: dict):
    """Fila estilizada para listar sesiones en activo o parked"""
    product = get_product(s["product_id"])
    module = get_module_for_session(s["id"])

    st.markdown(
        f"""
        <div style="
            padding:14px;
            background:white;
            border-radius:10px;
            border:1px solid {SOFT_BORDER};
            margin-bottom:10px;
        ">
            <div style="display:flex;justify-content:space-between;">
                <div>
                    <div style="font-size:16px;font-weight:600;color:{PRIMARY_BLUE};">
                        {product["name"] if product else "Producto desconocido"}
                    </div>

                    <div style="font-size:13px;color:#64748b;">
                        Sesión: {s["id"]}<br>
                        Estado: {s["status"]}<br>
                        Aforo: {s["pax_registered"]}/{s["capacity"]}
                    </div>

                    <div style="font-size:13px;margin-top:6px;color:#334155;">
                        Módulo: <strong>{module['module_code'] if module else 'N/A'}</strong>
                    </div>
                </div>

                <div style="text-align:right;">
                    <button style="
                        background:{PRIMARY_BLUE};
                        color:white;
                        padding:8px 14px;
                        border-radius:6px;
                        border:none;
                        cursor:pointer;
                    ">Ver Sesión</button>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =====================================
#   DASHBOARD PRINCIPAL FINTECH
# =====================================
def render_operator_dashboard_pro():
    st.markdown(
        """
        <h2 style="color:#1e40af; margin-bottom:4px;">Operator Dashboard Pro</h2>
        <p style="color:#64748b; margin-top:-10px;">
            Vista profesional estilo fintech (Revolut / MangoPay)
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar para elegir organización
    st.sidebar.subheader("Organization ID")
    organization_id = st.sidebar.text_input("Introduce tu Organization ID")

    if not organization_id:
        st.info("Introduce un **organization_id** para continuar.")
        return

    # =========================
    #      KPIs Principales
    # =========================
    col1, col2, col3 = st.columns(3)

    # Contadores básicos
    active_sessions = get_active_sessions()
    parked_sessions = get_parked_sessions()

    col1.markdown(_kpi_card("Sesiones Activas", str(len(active_sessions))), unsafe_allow_html=True)
    col2.markdown(_kpi_card("Sesiones Parked", str(len(parked_sessions))), unsafe_allow_html=True)
    col3.markdown(
        _kpi_card("Productos Activos", "—"), unsafe_allow_html=True
    )  # Lo rellenamos después

    st.markdown("<hr>", unsafe_allow_html=True)

    # =============================================
    #   SESIONES ACTIVAS (LISTA VISUAL PROFESIONAL)
    # =============================================
    st.markdown(
        f"""
        <h3 style="color:{PRIMARY_BLUE};">Sesiones Activas</h3>
        """,
        unsafe_allow_html=True,
    )

    if not active_sessions:
        st.info("No hay sesiones activas actualmente.")
    else:
        for s in active_sessions:
            _session_row(s)

    st.markdown("<hr>", unsafe_allow_html=True)

    # =============================================
    #   SESIONES PARKED
    # =============================================
    st.markdown(
        f"""
        <h3 style="color:{PRIMARY_BLUE};">Sesiones Parked</h3>
        """,
        unsafe_allow_html=True,
    )

    if not parked_sessions:
        st.info("No hay sesiones parked.")
    else:
        for s in parked_sessions:
            _session_row(s)

    st.markdown("<hr>", unsafe_allow_html=True)

    st.success("Panel Operador Pro cargado correctamente.")


