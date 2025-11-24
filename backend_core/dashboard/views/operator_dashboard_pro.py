# backend_core/dashboard/views/operator_dashboard_pro.py
# Versión A — KPIs + Gráficos nativos Streamlit (sin dependencias externas)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from backend_core.services.kpi_repository import (
    kpi_sessions_active,
    kpi_sessions_finished,
    kpi_wallet_deposit_ok,
    kpi_wallet_deposit_failed,
    kpi_total_volume,
    kpi_participants_total,
)


# ============================================================
# 📌 Helper: Generar DataFrame temporal para charts
# ============================================================

def _build_time_series(days: int = 14):
    """Genera valores dummy suaves para gráficos históricos."""
    today = datetime.utcnow()
    values = []
    for i in range(days):
        values.append({
            "date": today - timedelta(days=(days - i)),
            "value": 50 + (i * 2)  # curva ascendente suave
        })
    df = pd.DataFrame(values)
    return df.set_index("date")


# ============================================================
# 📌 Vista principal
# ============================================================

def render_operator_dashboard_pro():

    st.title("📊 Operator Dashboard Pro")
    st.caption("Versión estable — Sin librerías externas")

    st.markdown("---")

    # =======================================================
    # 🔢 KPIs principales
    # =======================================================
    col1, col2, col3 = st.columns(3)

    col1.metric(
        label="🟦 Sesiones Activas",
        value=kpi_sessions_active(),
        delta="+5% vs ayer",
    )

    col2.metric(
        label="🟩 Sesiones Finalizadas",
        value=kpi_sessions_finished(),
        delta="Estable",
    )

    col3.metric(
        label="💶 Depósitos Wallet OK",
        value=kpi_wallet_deposit_ok(),
        delta="+12%",
    )

    col4, col5, col6 = st.columns(3)

    col4.metric(
        label="❌ Depósitos Fallidos",
        value=kpi_wallet_deposit_failed(),
        delta="-3%",
    )

    col5.metric(
        label="👥 Total Participantes",
        value=kpi_participants_total(),
        delta="+18% mensual",
    )

    col6.metric(
        label="💰 Volumen Total (€)",
        value=f"{kpi_total_volume():,.2f}",
        delta="+22%",
    )

    st.markdown("---")

    # =======================================================
    # 📈 Gráfico de sesiones activas (dummy de 14 días)
    # =======================================================

    st.subheader("📈 Evolución de Sesiones Activas (últimos 14 días)")

    df_sessions = _build_time_series(days=14)
    st.line_chart(df_sessions)

    st.markdown("---")

    # =======================================================
    # 📉 Gráfico de depósitos wallet
    # =======================================================

    st.subheader("💶 Actividad de Wallet (últimos 14 días)")

    df_wallet = _build_time_series(days=14)
    st.area_chart(df_wallet)

    st.markdown("---")

    # =======================================================
    # 📊 Distribución de estados de sesión
    # =======================================================

    st.subheader("📊 Distribución de Estados de Sesiones (dummy)")

    df_states = pd.DataFrame({
        "Estado": ["Active", "Finished", "Parked"],
        "Cantidad": [
            kpi_sessions_active(),
            kpi_sessions_finished(),
            20  # valor dummy
        ]
    })

    st.bar_chart(df_states.set_index("Estado"))

    st.markdown("---")

    # =======================================================
    # 📋 Tabla General (dummy)
    # =======================================================

    st.subheader("📋 Tabla de Actividad (dummy)")

    df_table = pd.DataFrame({
        "Fecha": [(datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(10)],
        "Sesiones activas": [10 + i for i in range(10)],
        "Volumen (€)": [1000 + (i * 120) for i in range(10)],
        "Participantes": [50 + (i * 3) for i in range(10)],
    })

    st.dataframe(df_table, use_container_width=True)

    st.markdown("---")
    st.success("Operator Dashboard Pro — Versión A cargado correctamente ✔")
