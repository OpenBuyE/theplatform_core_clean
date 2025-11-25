# backend_core/dashboard/views/operator_dashboard_pro.py

import streamlit as st
import pandas as pd
from datetime import datetime

from backend_core.services.kpi_repository import (
    kpi_sessions_active,
    kpi_sessions_finished,
    kpi_sessions_expired,
    kpi_participants_total,
    kpi_modules_total,
    kpi_operators_total,
    kpi_payments_total,
)


def render_operator_dashboard_pro():
    st.title("📊 Operator Dashboard — PRO")
    st.write("Vista profesional con KPIs corporativos estilo fintech.")

    # -------------------------
    # TOP GRID DE KPIs
    # -------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Sesiones Activas", kpi_sessions_active())
        st.metric("Sesiones Finalizadas", kpi_sessions_finished())

    with col2:
        st.metric("Sesiones Expiradas", kpi_sessions_expired())
        st.metric("Total Participantes", kpi_participants_total())

    with col3:
        st.metric("Módulos Disponibles", kpi_modules_total())
        st.metric("Operadores", kpi_operators_total())

    st.divider()

    # -------------------------
    # SEGUNDA FILA KPI
    # -------------------------
    st.subheader("Pagos procesados")
    st.metric("Registro de pagos en sistema", kpi_payments_total())

    st.divider()

    # -------------------------
    # TABLA ESTILO CORPORATIVO
    # -------------------------
    st.subheader("📁 Ejemplo tabla en estilo corporativo")
    df = pd.DataFrame({
        "Fecha": [datetime.utcnow().strftime("%Y-%m-%d")],
        "Sesiones Activas": [kpi_sessions_active()],
        "Finalizadas": [kpi_sessions_finished()],
        "Expiradas": [kpi_sessions_expired()],
    })
    st.dataframe(df, use_container_width=True)

    st.info("Gráficos avanzados listos para activar cuando integramos Plotly.")
