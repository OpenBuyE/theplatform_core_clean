import streamlit as st
import pandas as pd

from backend_core.services.session_repository import get_active_sessions


def _apply_filters(rows: list[dict]) -> list[dict]:
    """
    Filtros para sesiones activas:
    - operador
    - proveedor/producto
    - estado (active, open, running)
    - búsqueda por ID
    """
    if not rows:
        return rows

    df = pd.DataFrame(rows)

    st.subheader("🔎 Filtros Sesiones Activas")

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

    # Estados (por si en el futuro hay más)
    statuses = sorted(
        [s for s in df.get("status", []).unique() if pd.notna(s)]
    )
    selected_statuses = st.multiselect(
        "Filtrar por estado",
        options=statuses,
        default=statuses,
    )

    # Búsqueda por ID
    search_id = st.text_input(
        "Buscar por ID de sesión (contiene)",
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

    if search_id:
        filtered = [
            r for r in filtered
            if search_id.lower() in str(r.get("id", "")).lower()
        ]

    return filtered


def _paginate_rows(rows: list[dict]) -> list[dict]:
    """
    Paginación en memoria para sesiones activas.
    """
    if not rows:
        return rows

    st.subheader("📄 Paginación")

    total = len(rows)
    default_page_size = 20 if total > 20 else total

    page_size = st.number_input(
        "Sesiones por página",
        min_value=5,
        max_value=100,
        value=default_page_size if default_page_size >= 5 else 5,
        step=5,
    )

    page_size = int(page_size) if page_size > 0 else 10
    total_pages = (total + page_size - 1) // page_size

    page = st.number_input(
        "Página",
        min_value=1,
        max_value=max(total_pages, 1),
        value=1,
        step=1,
    )

    page = int(page)
    start = (page - 1) * page_size
    end = start + page_size

    st.caption(f"Mostrando {min(end, total) - start} de {total} sesiones activas")

    return rows[start:end]


def render_active_sessions():
    st.header("🔥 Sesiones Activas")

    rows = get_active_sessions()

    if not rows:
        st.info("No hay sesiones activas actualmente.")
        return

    rows = _apply_filters(rows)

    if not rows:
        st.warning("No hay sesiones activas que cumplan los filtros seleccionados.")
        return

    rows = _paginate_rows(rows)

    for row in rows:
        st.markdown("### 🧾 Sesión activa")
        st.write(f"**ID:** `{row['id']}`")
        st.write(f"**Operador:** {row.get('operator_code', '-')}")
        st.write(f"**Proveedor / Producto:** {row.get('product_id', '-')}")
        st.write(f"**Estado:** `{row.get('status', '-')}`")
        st.write(f"**Importe:** {row.get('amount', 0)} €")
        st.write(f"**Cadena:** {row.get('chain_group_id', '-')}")
        st.write(f"**Creada:** {row.get('created_at', '-')}")
        st.write(f"**Actualizada:** {row.get('updated_at', '-')}")

        st.markdown("---")



