# backend_core/dashboard/views/operator_dashboard_pro.py

import streamlit as st
import plotly.express as px
from datetime import date, timedelta

from backend_core.services.kpi_repository import (
    kpi_count_active,
    kpi_count_finished,
    kpi_sum_deposits,
    kpi_timeseries_active,
    kpi_timeseries_deposits,
)

# ==============================
# COMPONENTE — CARD
# ==============================
def kpi_card(label: str, value: str, color="#1A73E8"):
    st.markdown(
        f"""
        <div style="
            padding: 18px;
            border-radius: 14px;
            background: white;
            border: 1px solid #e6e6e6;
            box-shadow: 0px 3px 10px rgba(0,0,0,0.05);
        ">
            <div style="font-size: 16px; color: #444;">{label}</div>
            <div style="font-size: 32px; font-weight: 600; color: {color}; margin-top: 6px;">
                {value}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================
# MAIN VIEW
# ==============================
def render_operator_dashboard_pro():

    st.title("📊 Operator Dashboard — PRO Edition")
    st.markdown("### Panel Fintech · Visión Ejecutiva")

    # --------------------------------------------
    # FILTER BAR (últimos N días)
    # --------------------------------------------
    st.write("")
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        days = st.selectbox("Rango de tiempo", [7, 15, 30], index=0)
    with col2:
        start_date = date.today() - timedelta(days=days)
        end_date = date.today()
        st.write(f"📅 Desde **{start_date}** hasta **{end_date}**")
    st.write("---")

    # --------------------------------------------
    # KPI CARDS
    # --------------------------------------------
    c1, c2, c3 = st.columns(3)

    with c1:
        active = kpi_count_active()
        kpi_card("Sesiones Activas", active, "#1A73E8")

    with c2:
        finished = kpi_count_finished()
        kpi_card("Sesiones Finalizadas", finished, "#34A853")

    with c3:
        deposits = kpi_sum_deposits()
        kpi_card("Depósitos Procesados (€)", f"{deposits:,.2f}", "#FB8C00")

    st.write("")

    # --------------------------------------------
    # TIMESERIES — Líneas sesiones activas por día
    # --------------------------------------------
    df_active = kpi_timeseries_active(start_date, end_date)

    if df_active is not None and len(df_active) > 0:
        fig1 = px.line(
            df_active,
            x="day",
            y="count",
            title="Sesiones Activas por Día",
            markers=True
        )
        st.plotly_chart(fig1, use_container_width=True)

    st.write("")

    # --------------------------------------------
    # TIMESERIES — Barras depósitos por día
    # --------------------------------------------
    df_dep = kpi_timeseries_deposits(start_date, end_date)

    if df_dep is not None and len(df_dep) > 0:
        fig2 = px.bar(
            df_dep,
            x="day",
            y="amount",
            title="Depósitos Procesados por Día (€)",
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.write("---")
    st.success("Panel cargado correctamente (Plotly, seguro, estable).")
