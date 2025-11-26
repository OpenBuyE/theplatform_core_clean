import streamlit as st

from backend_core.services.kpi_repository import (
    sessions_active,
    sessions_finished,
    sessions_expired,
    wallet_deposit_ok,
    wallets_total,
    providers_total,
    products_total,
    categories_total,
)

# ------------------------------------------------------------
# OPERATOR DASHBOARD (CLÁSICO)
# Versión Multi-país (usa operator_id del session_state)
# ------------------------------------------------------------

def render_operator_dashboard():
    st.title("📊 Operator Dashboard")

    # --------------------------------------------------------
    # REQUIERE LOGIN DE OPERADOR
    # --------------------------------------------------------
    operator_id = st.session_state.get("operator_id")

    if not operator_id:
        st.warning("⚠️ No hay operador seleccionado. Vaya a 'Login Operadores'.")
        return

    allowed_countries = st.session_state.get("allowed_countries")
    role = st.session_state.get("role")

    # Header con info del operador
    st.markdown(f"**Operador:** `{operator_id}`")
    st.markdown(f"**Rol:** `{role}`")

    if allowed_countries is None:
        st.markdown("**Países:** Acceso Global 🌍")
    else:
        st.markdown(f"**Países:** {', '.join(allowed_countries)}")

    st.markdown("---")

    # --------------------------------------------------------
    # KPIs PRINCIPALES
    # --------------------------------------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Sesiones Activas",
            sessions_active(operator_id)
        )

    with col2:
        st.metric(
            "Sesiones Finalizadas",
            sessions_finished(operator_id)
        )

    with col3:
        st.metric(
            "Sesiones Expiradas",
            sessions_expired(operator_id)
        )

    st.markdown("---")

    # --------------------------------------------------------
    # KPIs ECONÓMICOS / OPERATIVOS
    # --------------------------------------------------------
    col4, col5 = st.columns(2)

    with col4:
        st.metric(
            "Depósitos Confirmados",
            wallet_deposit_ok(operator_id)
        )

    with col5:
        st.metric(
            "Total Wallets",
            wallets_total(operator_id)
        )

    st.markdown("---")

    # --------------------------------------------------------
    # CATALOGO & PROVEEDORES
    # --------------------------------------------------------
    col6, col7, col8 = st.columns(3)

    with col6:
        st.metric(
            "Productos",
            products_total(operator_id)
        )

    with col7:
        st.metric(
            "Proveedores",
            providers_total(operator_id)
        )

    with col8:
        st.metric(
            "Categorías",
            categories_total(operator_id)
        )

    st.markdown("---")
    st.success("Dashboard actualizado con filtrado multi-país.")
