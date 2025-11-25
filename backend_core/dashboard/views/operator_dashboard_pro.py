# backend_core/dashboard/views/operator_dashboard_pro.py
# =======================================================
# Operator Dashboard PRO — White Clean Fintech Edition
# =======================================================

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

from backend_core.services.kpi_repository import (
    kpi_sessions_active,
    kpi_sessions_finished,
    kpi_sessions_expired,
    kpi_payment_deposit_ok,
    kpi_payment_deposit_failed,
    kpi_wallets_total,
)


# -------------------------------------------------------
# Helper UI Components
# -------------------------------------------------------

def _metric_card(title: str, value: str, icon: str = "📊"):
    """
    Render a simple fintech-style metric card.
    """
    st.markdown(
        f"""
        <div style="
            background-color:white;
            border-radius:12px;
            padding:20px;
            box-shadow:0 2px 10px rgba(0,0,0,0.06);
            border:1px solid #f2f2f2;
        ">
            <div style="font-size:28px; font-weight:600; color:#0d47a1; margin-bottom:4px;">
                {icon} {value}
            </div>
            <div style="font-size:15px; color:#444;">
                {title}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _section_title(text: str):
    st.markdown(
        f"""
        <h2 style="color:#0d47a1; margin-top:40px; margin-bottom:10px;">
            {text}
        </h2>
        """,
        unsafe_allow_html=True,
    )


# -------------------------------------------------------
# Main Render Function
# -------------------------------------------------------

def render_operator_dashboard_pro():
    st.markdown(
        """
        <h1 style="color:#0d47a1;">Operator Dashboard — Pro</h1>
        <p style="color:#555; margin-bottom:30px;">
            Vista profesional con KPIs operativos y analítica básica de actividad.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------
    # KPI ROW 1 — Sessions
    # ---------------------------------------------------
    _section_title("Estado de Sesiones")

    col1, col2, col3 = st.columns(3)

    with col1:
        _metric_card("Sesiones Activas", kpi_sessions_active(), "🟢")

    with col2:
        _metric_card("Sesiones Finalizadas", kpi_sessions_finished(), "🔵")

    with col3:
        _metric_card("Sesiones Expiradas", kpi_sessions_expired(), "🟡")

    # ---------------------------------------------------
    # KPI ROW 2 — Wallet & Payments
    # ---------------------------------------------------
    _section_title("Estado de Pagos y Carteras")

    col4, col5, col6 = st.columns(3)

    with col4:
        _metric_card("Depósitos Correctos", kpi_payment_deposit_ok(), "💶")

    with col5:
        _metric_card("Depósitos Fallidos", kpi_payment_deposit_failed(), "⚠️")

    with col6:
        _metric_card("Carteras Creadas", kpi_wallets_total(), "👛")

    # ---------------------------------------------------
    # Basic Data Panel — Example Fake Trend
    # (Until real historical data pipeline is connected)
    # ---------------------------------------------------
    _section_title("Actividad Reciente (Mock Temporal)")

    days = [datetime.utcnow() - timedelta(days=i) for i in range(7)]
    df = pd.DataFrame({
        "Fecha": [d.strftime("%Y-%m-%d") for d in reversed(days)],
        "Sesiones Activas": [kpi_sessions_active() for _ in range(7)],
        "Depósitos OK": [kpi_payment_deposit_ok() for _ in range(7)],
    })

    st.dataframe(df, use_container_width=True)

    # ---------------------------------------------------
    # End
    # ---------------------------------------------------
    st.markdown(
        """
        <p style="margin-top:40px; color:#999; font-size:13px;">
            Panel Pro — versión ligera optimizada para Streamlit Cloud.
        </p>
        """,
        unsafe_allow_html=True,
    )
