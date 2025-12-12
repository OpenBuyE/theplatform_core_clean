import streamlit as st
from datetime import datetime

from backend_core.services.kpi_repository import (
    get_kpi_sessions_active,
    get_kpi_sessions_finished,
    get_kpi_sessions_expired,
    get_kpi_wallets_total,
    get_kpi_providers_total,
    get_kpi_products_total,
    get_kpi_categories_total,
)
from backend_core.services.operator_repository import get_operator_info


# ======================================================================
# RENDER PRINCIPAL
# ======================================================================
def render_operator_dashboard():
    st.title("📊 Operator Dashboard")

    # ---------------------------------------------------------
    # Validación de login
    # ---------------------------------------------------------
    operator_id = st.session_state.get("operator_id")
    if not operator_id:
        st.error("Debe iniciar sesión como operador.")
        return

    # ---------------------------------------------------------
    # Obtener info del operador (SUPABASE v2 SAFE)
    # ---------------------------------------------------------
    operator = None
    try:
        resp = get_operator_info(operator_id)
        operator = resp.data if resp else None
    except Exception as e:
        st.error(f"Error cargando operador: {e}")
        return

    if not operator:
        st.error("No se pudo cargar la información del operador.")
        return

    country_list = operator.get("allowed_countries", ["ES"])
    role = operator.get("role", "operator")

    st.write(f"**Operador:** `{operator_id}` — Rol: **{role}**")
    st.write(f"**Países autorizados:** {', '.join(country_list)}")

    st.markdown("---")

    # ---------------------------------------------------------
    # Cargar KPIs multi-país filtrados por permisos
    # ---------------------------------------------------------
    try:
        kpi_active = get_kpi_sessions_active(operator_id)
        kpi_finished = get_kpi_sessions_finished(operator_id)
        kpi_expired = get_kpi_sessions_expired(operator_id)
        kpi_wallets = get_kpi_wallets_total(operator_id)
        kpi_providers = get_kpi_providers_total(operator_id)
        kpi_products = get_kpi_products_total(operator_id)
        kpi_categories = get_kpi_categories_total(operator_id)
    except Exception as e:
        st.error(f"Error cargando KPIs: {e}")
        return

    # =========================================================
    # TARJETAS KPI
    # =========================================================
    _kpi_row(
        [
            ("Sesiones Activas", kpi_active, "#3A6FF7"),
            ("Finalizadas", kpi_finished, "#20B858"),
            ("Expiradas", kpi_expired, "#F5A623"),
        ]
    )

    _kpi_row(
        [
            ("Productos", kpi_products, "#1A3DB5"),
            ("Categorías", kpi_categories, "#8B5CF6"),
            ("Proveedores", kpi_providers, "#3A3A3A"),
        ]
    )

    st.markdown("---")

    # =========================================================
    # Vista especializada según rol
    # =========================================================
    if role in ["admin_master", "admin_global"]:
        st.subheader("🔧 Panel Administrador (Master)")
        st.info("Acceso completo a todos los KPIs globales.")

    elif role == "country_admin":
        st.subheader("🌍 Panel Country Admin")
        st.info("Acceso a gestión y métricas exclusivamente de sus países.")

    else:
        st.subheader("👤 Panel Operador")
        st.info("Acceso limitado al país asignado y KPIs básicos.")


# ======================================================================
# RENDER DE FILAS KPI
# ======================================================================
def _kpi_row(kpis):
    cols = st.columns(len(kpis))
    for idx, (label, value, color) in enumerate(kpis):
        with cols[idx]:
            _kpi_card(label, value, color)


# ======================================================================
# TARJETA KPI INDIVIDUAL
# ======================================================================
def _kpi_card(label: str, value: int, color: str):
    st.markdown(
        f"""
        <div style="
            background-color: #FFFFFF;
            border-radius: 12px;
            padding: 15px;
            border: 1px solid #E5E5E5;
            box-shadow: 0 2px 4px rgba(0,0,0,0.06);
        ">
            <div style="font-size: 14px; color: {color}; font-weight: 600;">
                {label}
            </div>
            <div style="
                font-size: 32px;
                font-weight: 700;
                margin-top: 8px;
                color: #1A1A1A;">
                {value}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
