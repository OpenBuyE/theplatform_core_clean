import streamlit as st
import pandas as pd

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
from backend_core.services.session_repository import get_sessions


# ------------------------------------------------------------
# OPERATOR DASHBOARD PRO
# Versión multi-país + charts nativos Streamlit
# ------------------------------------------------------------

def render_operator_dashboard_pro():
    st.title("📈 Operator Dashboard PRO")

    # --------------------------------------------------------
    # 1. REQUIERE LOGIN DE OPERADOR
    # --------------------------------------------------------
    operator_id = st.session_state.get("operator_id")

    if not operator_id:
        st.warning("⚠️ No hay operador seleccionado. Vaya a 'Operator Login' para iniciar sesión.")
        return

    role = st.session_state.get("role", "unknown")
    allowed_countries = st.session_state.get("allowed_countries")
    global_access = st.session_state.get("global_access", False)

    # Header info
    st.markdown(f"**Operador:** `{operator_id}`")
    st.markdown(f"**Rol:** `{role}`")

    if global_access or allowed_countries is None:
        st.markdown("**Países:** Acceso Global 🌍")
    else:
        st.markdown(f"**Países:** {', '.join(allowed_countries)}")

    st.markdown("---")

    # --------------------------------------------------------
    # 2. KPIs PRINCIPALES (SESSIONS)
    # --------------------------------------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Sesiones Activas",
            value=sessions_active(operator_id),
        )

    with col2:
        st.metric(
            label="Sesiones Finalizadas",
            value=sessions_finished(operator_id),
        )

    with col3:
        st.metric(
            label="Sesiones Expiradas",
            value=sessions_expired(operator_id),
        )

    st.markdown("")

    # --------------------------------------------------------
    # 3. KPIs ECONÓMICOS / WALLET
    # --------------------------------------------------------
    col4, col5 = st.columns(2)

    with col4:
        st.metric(
            label="Depósitos Confirmados",
            value=wallet_deposit_ok(operator_id),
        )

    with col5:
        st.metric(
            label="Total Wallets (estimado)",
            value=wallets_total(operator_id),
        )

    st.markdown("")

    # --------------------------------------------------------
    # 4. KPIs DE CATÁLOGO
    # --------------------------------------------------------
    col6, col7, col8 = st.columns(3)

    with col6:
        st.metric(
            label="Productos",
            value=products_total(operator_id),
        )

    with col7:
        st.metric(
            label="Proveedores",
            value=providers_total(operator_id),
        )

    with col8:
        st.metric(
            label="Categorías",
            value=categories_total(operator_id),
        )

    st.markdown("---")

    # --------------------------------------------------------
    # 5. CARGA DE SESIONES PARA CHARTS
    # --------------------------------------------------------
    try:
        sessions = get_sessions(operator_id)
    except Exception as e:
        st.error(f"No se han podido cargar las sesiones para análisis PRO: {e}")
        return

    if not sessions:
        st.info("No hay sesiones disponibles para mostrar gráficos.")
        return

    # Normalizamos en DataFrame para análisis
    df = pd.DataFrame(sessions)

    # Asegurar columnas esperadas
    if "status" not in df.columns:
        st.error("El dataset de sesiones no contiene el campo 'status'.")
        return

    # created_at puede no existir o venir vacío
    if "created_at" in df.columns:
        # Convertimos a fecha (ignorando errores)
        df["created_at_parsed"] = pd.to_datetime(df["created_at"], errors="coerce")
        df["created_date"] = df["created_at_parsed"].dt.date
    else:
        df["created_date"] = pd.NaT

    # --------------------------------------------------------
    # 6. DISTRIBUCIÓN POR ESTADO
    # --------------------------------------------------------
    st.subheader("Distribución de Sesiones por Estado")

    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]

    if not status_counts.empty:
        st.dataframe(status_counts, use_container_width=False)
        st.bar_chart(
            data=status_counts.set_index("status")["count"]
        )
    else:
        st.info("No hay datos suficientes para la distribución por estado.")

    st.markdown("---")

    # --------------------------------------------------------
    # 7. EVOLUCIÓN POR FECHA (si hay created_date)
    # --------------------------------------------------------
    if df["created_date"].notna().any():
        st.subheader("Evolución de Sesiones por Fecha")

        date_counts = (
            df[df["created_date"].notna()]
            .groupby("created_date")["id"]
            .count()
            .reset_index()
        )
        date_counts.columns = ["date", "sessions"]

        if not date_counts.empty:
            st.line_chart(
                data=date_counts.set_index("date")["sessions"]
            )
        else:
            st.info("No hay datos suficientes para la evolución temporal.")
    else:
        st.info("Las sesiones no tienen campo 'created_at' utilizable para gráficos de tiempo.")

    st.markdown("---")

    # --------------------------------------------------------
    # 8. RESUMEN FINAL
    # --------------------------------------------------------
    st.success("Operator Dashboard PRO cargado con KPIs multi-país y gráficos operativos.")
