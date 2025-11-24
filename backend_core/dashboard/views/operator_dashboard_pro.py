# backend_core/dashboard/views/operator_dashboard_pro.py

import streamlit as st
import plotly.express as px

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

PRIMARY_BLUE = "#2563eb"
GREEN = "#16a34a"
ORANGE = "#ea580c"


# ==============================
# COMPONENTE — CARD KPI
# ==============================
def kpi_card(label: str, value: str, color: str = PRIMARY_BLUE):
    st.markdown(
        f"""
        <div style="
            padding: 18px;
            border-radius: 14px;
            background: white;
            border: 1px solid #e5e7eb;
            box-shadow: 0 2px 8px rgba(15,23,42,0.06);
        ">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 4px;">
                {label}
            </div>
            <div style="font-size: 30px; font-weight: 600; color: {color};">
                {value}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==============================
# VISTA PRINCIPAL
# ==============================
def render_operator_dashboard_pro():
    # Header
    st.markdown(
        f"""
        <h2 style="color:#0f172a; margin-bottom:2px;">
            Operator Dashboard PRO
        </h2>
        <p style="color:#64748b; margin-top:0;">
            Vista ejecutiva estilo fintech (Revolut / MangoPay): sesiones, pagos y salud de la plataforma.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    # ==========================
    # KPI CARDS
    # ==========================
    col1, col2, col3, col4, col5 = st.columns(5)

    try:
        active = kpi_sessions_active()
    except Exception:
        active = 0

    try:
        finished = kpi_sessions_finished()
    except Exception:
        finished = 0

    try:
        deposits_ok = kpi_wallet_deposit_ok()
    except Exception:
        deposits_ok = 0

    try:
        settlements = kpi_wallet_settlement_completed()
    except Exception:
        settlements = 0

    try:
        fm_refunds = kpi_wallet_force_majeure()
    except Exception:
        fm_refunds = 0

    with col1:
        kpi_card("Sesiones activas", str(active), PRIMARY_BLUE)
    with col2:
        kpi_card("Sesiones finalizadas", str(finished), GREEN)
    with col3:
        kpi_card("Depósitos OK", str(deposits_ok), ORANGE)
    with col4:
        kpi_card("Settlements completados", str(settlements), GREEN)
    with col5:
        kpi_card("Force majeure refund", str(fm_refunds), "#7c3aed")

    st.markdown("---")

    # ==========================
    # GRÁFICO 1 — Sesiones por módulo
    # ==========================
    st.subheader("Sesiones por módulo")

    try:
        mod_stats = kpi_sessions_by_module()
    except Exception:
        mod_stats = {}

    if not mod_stats:
        st.info("No hay sesiones asignadas a módulos todavía.")
    else:
        module_ids = list(mod_stats.keys())
        counts = list(mod_stats.values())

        fig_mod = px.bar(
            x=module_ids,
            y=counts,
            labels={"x": "Módulo", "y": "Número de sesiones"},
            title="Número de sesiones por módulo",
        )
        st.plotly_chart(fig_mod, use_container_width=True)

    st.markdown("---")

    # ==========================
    # GRÁFICO 2 — Evolución eventos de auditoría
    # ==========================
    st.subheader("Evolución de eventos de auditoría")

    try:
        audit_stats = kpi_audit_events_by_day()
    except Exception:
        audit_stats = {}

    if not audit_stats:
        st.info("No hay eventos de auditoría registrados todavía.")
    else:
        days = sorted(audit_stats.keys())
        counts = [audit_stats[d] for d in days]

        fig_audit = px.line(
            x=days,
            y=counts,
            markers=True,
            labels={"x": "Fecha", "y": "Eventos"},
            title="Eventos de auditoría por día",
        )
        fig_audit.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_audit, use_container_width=True)

    st.markdown("---")

    # ==========================
    # GRÁFICO 3 — Distribución estados de sesión
    # ==========================
    st.subheader("Distribución de estados de sesión")

    try:
        status_stats = kpi_sessions_status_distribution()
    except Exception:
        status_stats = {}

    if not status_stats:
        st.info("No hay sesiones registradas todavía.")
    else:
        labels = list(status_stats.keys())
        values = list(status_stats.values())

        fig_status = px.pie(
            names=labels,
            values=values,
            title="Estados de las sesiones",
        )
        st.plotly_chart(fig_status, use_container_width=True)

    st.success("Operator Dashboard PRO cargado correctamente.")
