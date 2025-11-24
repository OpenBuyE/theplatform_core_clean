# backend_core/dashboard/views/operator_dashboard_pro.py

import streamlit as st
import matplotlib.pyplot as plt

from backend_core.services.kpi_repository import (
    kpi_sessions_active,
    kpi_sessions_finished,
    kpi_wallet_deposit_ok,
    kpi_wallet_settlement_completed,
    kpi_wallet_force_majeure,
    kpi_sessions_by_module,
    kpi_audit_events_by_day,
    kpi_sessions_status_distribution,
)


# ==========================
# KPI CARD COMPONENT
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
    # GRAPH 1 — Sesiones por módulo (BARRAS)
    # ==========================
    st.markdown("---")
    st.subheader("Sesiones por módulo")

    mod_stats = kpi_sessions_by_module()

    if mod_stats:
        fig, ax = plt.subplots()
        codes = list(mod_stats.keys())
        counts = list(mod_stats.values())

        ax.bar(codes, counts)
        ax.set_title("Sesiones por módulo")
        ax.set_xlabel("Módulo")
        ax.set_ylabel("Número de sesiones")

        st.pyplot(fig)
    else:
        st.info("No hay sesiones asignadas a módulos.")

    # ==========================
    # GRAPH 2 — Evolución de auditoría (LÍNEA)
    # ==========================
    st.markdown("---")
    st.subheader("Evolución de eventos (Audit Trail)")

    audit_stats = kpi_audit_events_by_day()

    if audit_stats:
        days = sorted(audit_stats.keys())
        values = [audit_stats[d] for d in days]

        fig, ax = plt.subplots()
        ax.plot(days, values, marker="o")
        ax.set_title("Eventos de auditoría por día")
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Eventos")

        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.info("Sin eventos de auditoría todavía.")

    # ==========================
    # GRAPH 3 — Distribución de sesiones por estado (TARTA)
    # ==========================
    st.markdown("---")
    st.subheader("Distribución de estado de sesiones")

    session_status = kpi_sessions_status_distribution()
    if session_status:
        labels = list(session_status.keys())
        sizes = list(session_status.values())

        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140)
        ax.set_title("Distribución de estados de sesiones")

        st.pyplot(fig)
    else:
        st.info("No existen sesiones registradas todavía.")
