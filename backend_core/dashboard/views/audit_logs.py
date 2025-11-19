import streamlit as st
import pandas as pd
from backend_core.services.audit_repository import fetch_logs


def render_audit_logs():
    st.header("📘 Registro de Auditoría")

    rows = fetch_logs()

    if not rows:
        st.info("No hay registros de auditoría.")
        return

    df = pd.DataFrame(rows)

    # Normalizar campos
    if "performed_at" in df.columns:
        df["performed_at"] = pd.to_datetime(df["performed_at"])

    # --- Filtros ---
    st.subheader("🔎 Filtros")

    # Acción
    actions = sorted(df["action"].dropna().unique().tolist())
    selected_actions = st.multiselect(
        "Acción",
        options=actions,
        default=actions,
    )

    # Usuario
    users = sorted(df["performed_by"].dropna().unique().tolist())
    selected_users = st.multiselect(
        "Usuario",
        options=users,
        default=users,
    )

    # Sesión
    search_session = st.text_input(
        "Buscar por ID de sesión",
        "",
    ).strip()

    # Fechas
    min_date = df["performed_at"].min()
    max_date = df["performed_at"].max()

    date_range = st.date_input(
        "Rango de fechas",
        (min_date.date(), max_date.date()),
    )

    filtered = df.copy()

    # Aplicar filtros
    if selected_actions:
        filtered = filtered[filtered["action"].isin(selected_actions)]

    if selected_users:
        filtered = filtered[filtered["performed_by"].isin(selected_users)]

    if search_session:
        filtered = filtered[
            filtered["session_id"].str.contains(search_session, case=False, na=False)
        ]

    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered = filtered[
            (filtered["performed_at"].dt.date >= start_date)
            & (filtered["performed_at"].dt.date <= end_date)
        ]

    st.write(f"### 📄 {len(filtered)} registros encontrados")

    st.dataframe(filtered, use_container_width=True)
