# backend_core/dashboard/views/operator_dashboard_pro.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from backend_core.services.kpi_repository import (
    kpi_sessions_active,
    kpi_sessions_finished,
    kpi_sessions_expired,
    kpi_wallet_deposit_ok,
    kpi_wallet_deposit_failed,
    kpi_wallet_refunds,
    kpi_wallet_pending,
)


def _metric(label: str, value: int, color: str = "#2563eb"):
    """
    Bloque de métrica tipo fintech simple.
    """
    st.markdown(
        f"""
        <div style="
            background-color:white;
            border-radius:12px;
            padding:20px;
            border:1px solid #e5e7eb;
            box-shadow:0 1px 2px rgba(0,0,0,0.05);
        ">
            <div style="font-size:14px;color:#6b7280;">{label}</div>
            <div style="font-size:28px;font-weight:700;color:{color};">
                {value}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_operator_dashboard_pro():
    st.title("📊 Operator Dashboard Pro — Fintech Mode")

    st.write("KPIs agregados reales sobre sesiones, pagos y actividad operativa.")

    st.markdown("---")

    colA, colB, colC = st.columns(3)
    with colA:
        _metric("Sesiones Activas", kpi_sessions_active())
    with colB:
        _metric("Finalizadas", kpi_sessions_finished())
    with colC:
        _metric("Expiradas", kpi_sessions_expired())

    st.markdown("## 💰 Estado Pagos")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        _metric("Depósitos OK", kpi_wallet_deposit_ok(), "#16a34a")

    with col2:
        _metric("Depósitos Fallidos", kpi_wallet_deposit_failed(), "#dc2626")

    with col3:
        _metric("Reembolsos", kpi_wallet_refunds(), "#d97706")

    with col4:
        _metric("Pendientes", kpi_wallet_pending(), "#2563eb")

    st.markdown("---")

    st.write("Versión Pro con KPIs reales usando solo widgets nativos de Streamlit.")
