import streamlit as st
import pandas as pd

from backend_core.services.audit_repository import fetch_logs
from backend_core.services.acl import (
    require_org,
    require_permission
)


@require_org
@require_permission("audit.view")
def render_audit_logs():

    st.header("📘 Registro de Auditoría")

    rows = fetch_logs()

    if not rows:
        st.info("No hay registros de auditoría.")
        return

    df = pd.DataFrame(rows)

    if "performed_at" in df.columns:
        df["performed_at"] = pd.to_datetime(df["performed_at"])

    st.subheader("🔎 Filtros")

    # Acción
    actions = sorted(df["action"].dropna().unique().tolist())
    selected_actions = st.multiselect(
        "Acción", actions, default=actions
    )

    # Usuario
    users = sorted(df["performed_by"].dropna().unique().tolist())
    selected_users = st.multiselect(
        "Usuario", users, default=users
    )

    # Sesión
    session_filter = st.text_input("Buscar ID de sesión").strip()

    # Fechas
    min_date = df["performed_at"].min()
    max_date = df["performed_at"].max()

    date_range = st.date_input(
        "Rango de fechas",
        (min_date.date(), max_date.date())
    )

    filtered = df.copy()

    if selected_actions:
        filtered = filtered[filtered["action"].isin(selected_actions)]

    if selected_users:
        filtered = filtered[filtered["performed_by"].isin(selected_users)]

    if session_filter:
        filtered = filtered[
            filtered["session_id"].str.contains(session_filter, case=False, na=False)
        ]

    if len(date_range) == 2:
        start, end = date_range
        filtered = filtered[
            (filtered["performed_at"].dt.date >= start)
            &
            (filtered["performed_at"].dt.date <= end)
        ]

    st.write(f"### {len(filtered)} registros encontrados")
    st.dataframe(filtered, use_container_width=True)

