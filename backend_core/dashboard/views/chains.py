import streamlit as st
import pandas as pd
from collections import defaultdict

from backend_core.services.session_repository import get_chains


def _apply_filters(rows: list[dict]) -> list[dict]:
    """
    Filtros para sesiones con cadena:
    - operador
    - proveedor
    - estado
    - búsqueda por ID de cadena (chain_group_id)
    """
    if not rows:
        return rows

    df = pd.DataFrame(rows)

    st.subheader("🔎 Filtros Cadenas Operativas")

    # Operador
    operators = sorted(
        [op for op in df.get("operator_code", []).unique() if pd.notna(op)]
    )
    selected_operators = st.multiselect(
        "Filtrar por operador",
        options=operators,
        default=operators,
    )

    # Proveedor / producto
    products = sorted(
        [p for p in df.get("product_id", []).unique() if pd.notna(p)]
    )
    selected_products = st.multiselect(
        "Filtrar por proveedor / producto",
        options=products,
        default=products,
    )

    # Estado
    statuses = sorted(
        [s for s in df.get("status", []).unique() if pd.notna(s)]
    )
    selected_statuses = st.multiselect(
        "Filtrar por estado",
        options=statuses,
        default=statuses,
    )

    # Búsqueda por ID de cadena
    search_chain = st.text_input(
        "Buscar por ID de cadena (chain_group_id, contiene)",
        "",
    ).strip()

    filtered = rows

    if selected_operators:
        filtered = [
            r for r in filtered
            if r.get("operator_code") in selected_operators
        ]

    if selected_products:
        filtered = [
            r for r in filtered
            if r.get("product_id") in selected_products
        ]

    if selected_statuses:
        filtered = [
            r for r in filtered
            if r.get("status") in selected_statuses
        ]

    if search_chain:
        filtered = [
            r for r in filtered
            if search_chain.lower() in str(r.get("chain_group_id", "")).lower()
        ]

    return filtered


def render_chains():
    st.header("🔗 Cadenas Operativas")

    rows = get_chains()

    if not rows:
        st.info("No hay sesiones con cadena asignada.")
        return

    rows = _apply_filters(rows)

    if not rows:
        st.warning("No hay cadenas que cumplan los filtros seleccionados.")
        return

    # Agrupar por chain_group_id
    chains_map: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        chain_id = row.get("chain_group_id", "SIN_CADENA")
        chains_map[chain_id].append(row)

    # Ordenamos por ID de cadena
    for chain_id in sorted(chains_map.keys(), key=lambda x: str(x)):
        chain_sessions = chains_map[chain_id]

        st.markdown(f"## 🧬 Cadena: `{chain_id}`")
        st.caption(f"{len(chain_sessions)} sesiones en esta cadena")
        st.markdown("---")

        for row in chain_sessions:
            st.markdown("### 🧾 Sesión en cadena")
            st.write(f"**ID:** `{row['id']}`")
            st.write(f"**Operador:** {row.get('operator_code', '-')}")
            st.write(f"**Proveedor / Producto:** {row.get('product_id', '-')}")
            st.write(f"**Estado:** `{row.get('status', '-')}`")
            st.write(f"**Importe:** {row.get('amount', 0)} €")
            st.write(f"**Creada:** {row.get('created_at', '-')}")
            st.write(f"**Actualizada:** {row.get('updated_at', '-')}")

            st.markdown("---")


