import streamlit as st
import pandas as pd

from backend_core.services.session_repository import (
    get_sessions,
    activate_session,
)


def _apply_filters(rows: list[dict]) -> list[dict]:
    """
    Aplica filtros en memoria sobre la lista de sesiones 'parked'.
    Esto evita complejidad en las consultas y mantiene el panel robusto.
    """
    if not rows:
        return rows

    df = pd.DataFrame(rows)

    st.subheader("🔎 Filtros Parque de Sesiones")

    # Operador
    operators = sorted(
        [op for op in df.get("operator_code", []).unique() if pd.notna(op)]
    )
    selected_operators = st.multiselect(
        "Filtrar por operador",
        options=operators,
        default=operators,
        help="Selecciona uno o varios operadores. Si no seleccionas ninguno, se mostrarán todos.",
    )

    # Proveedor / producto
    products = sorted(
        [p for p in df.get("product_id", []).unique() if pd.notna(p)]
    )
    selected_products = st.multiselect(
        "Filtrar por proveedor / producto",
        options=products,
        default=products,
        help="Selecciona uno o varios productos. Si no seleccionas ninguno, se mostrarán todos.",
    )

    # Búsqueda por ID de sesión
    search_id = st.text_input(
        "Buscar por ID de sesión (contiene)",
        "",
        help="Escribe parte del ID para filtrar las sesiones.",
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

    if search_id:
        filtered = [
            r for r in filtered
            if search_id.lower() in str(r.get("id", "")).lower()
        ]

    return filtered


def _paginate_rows(rows: list[dict]) -> list[dict]:
    """
    Pagina la lista de sesiones en memoria.
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

    # Evitar división por cero
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

    st.caption(f"Mostrando {min(end, total) - start} de {total} sesiones")

    return rows[start:end]


def render_park_sessions():
    st.header("🅿️ Parque de Sesiones")

    rows = get_sessions()

    if not rows:
        st.info("No hay sesiones en estado 'parked'.")
        return

    # Filtros en memoria
    rows = _apply_filters(rows)

    if not rows:
        st.warning("No hay sesiones que cumplan los filtros seleccionados.")
        return

    # Paginación simple
    rows = _paginate_rows(rows)





