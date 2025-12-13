import streamlit as st
from typing import Dict, Any, List

from backend_core.services.showcase_service import list_active_showcases
from backend_core.services.supabase_client import table


# ==========================================================
# VIEW: SHOWCASES ACTIVOS (ADMIN)
# ==========================================================

def render_showcases():
    st.title("🟦 Showcases activos")
    st.caption("Producto + sesión activa (panel interno)")

    # ------------------------------------------------------
    # Filtros
    # ------------------------------------------------------
    with st.expander("🔍 Filtros", expanded=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            categories = _load_categories()
            category_map = {"Todas": None}
            for c in categories:
                category_map[c["name"]] = c["id"]

            selected_label = st.selectbox(
                "Categoría",
                options=list(category_map.keys()),
                index=0,
            )

            category_id = category_map[selected_label]

        with col2:
            limit = st.number_input(
                "Máx. resultados",
                min_value=5,
                max_value=100,
                value=20,
                step=5,
            )

    # ------------------------------------------------------
    # Datos
    # ------------------------------------------------------
    showcases = list_active_showcases(
        category_id=category_id,
        limit=int(limit),
        offset=0,
    )

    # ------------------------------------------------------
    # Render
    # ------------------------------------------------------
    if not showcases:
        st.info("No hay showcases activos en este momento.")
        return

    st.markdown(f"**{len(showcases)} showcase(s) activos**")

    for sc in showcases:
        _render_showcase_card(sc)
        st.divider()


# ==========================================================
# HELPERS UI
# ==========================================================

def _render_showcase_card(sc: Dict[str, Any]):
    product = sc["product"]
    session = sc["session"]

    with st.container(border=True):
        col_img, col_info, col_prog = st.columns([1, 2, 2])

        # Imagen
        with col_img:
            if product.get("image_url"):
                st.image(product["image_url"], use_column_width=True)
            else:
                st.markdown("🖼️ *Sin imagen*")

        # Info
        with col_info:
            st.subheader(product["name"])
            st.caption(f"Producto ID: {product['id']}")
            st.text(f"Sesión ID: {session['session_id']}")
            st.text(f"Estado: {session['status']}")
            st.text(f"Creada: {session['created_at']}")

        # Progreso
        with col_prog:
            st.markdown("**Aforo**")
            _progress_bar(session["filled_units"], session["capacity"])


def _progress_bar(filled: int, capacity: int):
    if capacity <= 0:
        st.progress(0)
        return

    pct = min(filled / capacity, 1.0)
    st.progress(pct)
    st.caption(f"{filled} / {capacity} ({round(pct * 100, 2)}%)")


@st.cache_data(ttl=30)
def _load_categories() -> List[Dict[str, Any]]:
    try:
        rows = table("categorias_v2").select("id, name").order("name").execute().data or []
        return rows
    except Exception:
        return []


# ==========================================================
# ENTRYPOINT ESTÁNDAR PARA ROUTER
# ==========================================================

def render():
    render_showcases()
