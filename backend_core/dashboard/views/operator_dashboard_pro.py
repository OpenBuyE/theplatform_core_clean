# backend_core/dashboard/views/operator_dashboard_pro.py

import streamlit as st

from backend_core.services.kpi_repository import (
    kpi_sessions_active,
    kpi_sessions_finished,
    kpi_wallet_deposit_ok,
    kpi_wallet_settlement_completed,
    kpi_wallet_force_majeure,
    kpi_sessions_by_module,
)


# ==========================
# CARD COMPONENT
# ==========================
def card(label, value, color="#1A73E8"):
    st.markdown(
        f"""
        <div style="
            padding: 20px;
            border-radius: 14px;
            background: white;
            border: 1px solid #E5E5E5;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        ">
            <div style="font-size: 15px; color: #666;">{label}</div>
            <div style="font-size: 32px; margin-top: 4px; color:{color}; font-weight: 700;">
                {value}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================
# OPERATOR DASHBOARD PRO
# ==========================
def render_operator_dashboard_pro():
    st.title("Operator Dashboard Pro — KPIs Fintech")
    st.markdown("### Vista profesional con métricas clave")

    # ==========================
    # KPI CARDS
    # ==========================
    active = kpi_sessions_active()
    finished = kpi_sessions_finished()
    deposits = kpi_wallet_deposit_ok()
    settlements = kpi_wallet_settlement_completed()
    fm_refunds = kpi_wallet_force_majeure()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        card("Sesiones Activas", active)

    with col2:
        card("Sesiones Finalizadas", finished)

    with col3:
        card("Deposit OK", deposits)

    with col4:
        card("Settlements", settlements)

    with col5:
        card("Force Majeure", fm_refunds)

    # ==========================
    # SESSIONS BY MODULE
    # ==========================
    st.markdown("---")
    st.subheader("Sesiones por módulo")

    mod_stats = kpi_sessions_by_module()
    if not mod_stats:
        st.info("No hay sesiones asignadas a módulos todavía.")
    else:
        for m, count in mod_stats.items():
            st.write(f"**Módulo {m}** → {count} sesiones")

