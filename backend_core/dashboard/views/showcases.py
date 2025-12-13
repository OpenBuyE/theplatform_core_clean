# backend_core/dashboard/views/showcases.py
import streamlit as st
from typing import Dict, Any, List

from backend_core.services.showcase_service import list_active_showcases
from backend_core.services.supabase_client import table


# ======================================================================
# RENDER PRINCIPAL
# ======================================================================
def render_showcases():
    st.title("🟦 Showcases (Producto + Sesión activa)")
    st.caption("Panel interno (backend/admin). Solo lectura.")

    # Operador debe estar logueado (misma política que otras vistas)
    operator_id = st.session_state.get("operator_id")
    if not operator_id:
        st.error("Debe iniciar sesión como operador.")
        return

    with st.expander("🔍 Filtros", expanded=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            categories = _load_categories()
            category_map = {"Todas": None}
            for c in categories:
                # categorias_v2: id, name (según tu esquema)
                category_map[c["name"]] = c["id"]

            selected_label = st.selectbox(
                "Categoría",
                options=list(category_map.keys()),
                index=0,
            )
            category_id = category_map[selected_label]

        with col2:
            limit = st.number_input("Máx. resultados", min_value=5, max_value=200, value=30, step=5)

    try:
        showcases = list_active_showcases(category_id=category_id, limit=int(limit), offset=0)
    except Exception as e:
        st.error(f"Error cargando showcases: {e}")
        return

    if not showcases:
        st.info("No hay sesiones activas (showcases) en este momento.")
        return

    st.success(f"Showcases activos: {len(showcases)}")

    for sc in showcases:
        _render_showcase_card(sc)
        st.divider()


# ======================================================================
# UI Helpers
# ======================================================================
def _render_showcase_card(sc: Dict[str, Any]):
    product = sc.get("product", {})
    session = sc.get("session", {})

    with st.container(border=True):
        col_img, col_info, col_prog = st.columns([1, 2, 2])

        with col_img:
            img = product.get("image_url")
            if img:
                st.image(img, use_column_width=True)
            else:
                st.markdown("🖼️ *Sin imagen*")

        with col_info:
            st.subheader(product.get("name", "Producto"))
            st.caption(f"Producto ID: {product.get('id')}")
            st.write(f"Sesión ID: `{session.get('session_id')}`")
            st.write(f"Estado: `{session.get('status')}`")
            st.write(f"Creada: {session.get('created_at')}")

            # Si hay precio (depende de products_v2)
            price = product.get("price_public")
            if price is not None:
                st.write(f"Precio: {price}")

        with col_prog:
            st.markdown("**Aforo**")
            filled = int(session.get("filled_units") or 0)
            capacity = int(session.get("capacity") or 0)
            _progress_bar(filled, capacity)


def _progress_bar(filled: int, capacity: int):
    if capacity <= 0:
        st.progress(0)
        st.caption("0 / 0")
        return
    pct = min(filled / capacity, 1.0)
    st.progress(pct)
    st.caption(f"{filled} / {capacity} ({round(pct * 100, 2)}%)")


@st.cache_data(ttl=60)
def _load_categories() -> List[Dict[str, Any]]:
    """
    categorias_v2 existe en tu DB. Si por lo que sea falla, devolvemos lista vacía.
    """
    try:
        return table("categorias_v2").select("id, name").order("name").execute().data or []
    except Exception:
        return []
