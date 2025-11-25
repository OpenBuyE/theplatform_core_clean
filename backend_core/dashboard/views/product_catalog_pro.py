# backend_core/dashboard/views/product_catalog_pro.py

import streamlit as st
import math

from backend_core.services.product_repository_v2 import (
    list_products,
    list_categories,
    filter_products,
)

from backend_core.dashboard.views.product_details_pro import (
    render_product_details_pro,
)


# ============================================
# CONTROLLER PRINCIPAL
# ============================================

def render_product_catalog_pro():
    """
    Punto de entrada: decide si mostrar catálogo o ficha de producto.
    """

    # Inicializamos session_state si no existe
    if "catalog_view" not in st.session_state:
        st.session_state["catalog_view"] = "catalog"
    if "catalog_product_id" not in st.session_state:
        st.session_state["catalog_product_id"] = None

    # Si estamos en modo 'details'
    if st.session_state["catalog_view"] == "details":
        _render_product_details_page()
        return

    # Si estamos en modo 'catalog'
    _render_catalog_page()


# ============================================
# PÁGINA DE DETALLES
# ============================================

def _render_product_details_page():
    st.button("⬅ Volver al catálogo", on_click=_go_back_to_catalog)

    product_id = st.session_state["catalog_product_id"]
    render_product_details_pro(product_id)


def _go_back_to_catalog():
    st.session_state["catalog_view"] = "catalog"
    st.session_state["catalog_product_id"] = None


# ============================================
# PÁGINA DE CATÁLOGO
# ============================================

def _render_catalog_page():
    st.title("📦 Catálogo de Productos PRO")

    categories = list_categories()

    # Sidebar Filtros
    with st.sidebar:
        st.header("🔍 Filtros")

        category_map = {c.get("name", c.get("id")): c["id"] for c in categories}
        selected_category = st.selectbox("Categoría", ["Todas"] + list(category_map.keys()))

        min_price = st.number_input("Precio mínimo", min_value=0.0, step=1.0, value=0.0)
        max_price = st.number_input("Precio máximo", min_value=0.0, step=1.0, value=10000.0)

        search = st.text_input("Buscar por nombre")

        apply = st.button("Aplicar filtros")

    # Aplicación de filtros
    if apply:
        category_id = None if selected_category == "Todas" else category_map[selected_category]
        products = filter_products(
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            search=search,
        )
    else:
        products = list_products()

    # Render cards
    if not products:
        st.info("No hay productos con estos filtros.")
        return

    _render_product_cards(products)


# ============================================
# GRID DE TARJETAS
# ============================================

def _render_product_cards(products):
    st.subheader(f"Mostrando {len(products)} productos")

    cols_per_row = 3
    rows = math.ceil(len(products) / cols_per_row)

    index = 0
    for _ in range(rows):
        cols = st.columns(cols_per_row)

        for col in cols:
            if index >= len(products):
                break

            product = products[index]
            index += 1

            with col:
                _render_single_product_card(product)


# ============================================
# TARJETA INDIVIDUAL
# ============================================

def _render_single_product_card(product):
    st.markdown("----")

    # Imagen
    if product.get("image_url"):
        st.image(product["image_url"], use_column_width=True)

    st.markdown(f"### {product['name']}")

    st.markdown(
        f"""
        **Precio:** {product['price_final']} €  
        **SKU:** {product.get('sku', '—')}
        """
    )

    # Botón "Ver ficha"
    if st.button(f"Ver ficha — {product['id'][:6]}"):
        st.session_state["catalog_view"] = "details"
        st.session_state["catalog_product_id"] = product["id"]
        st.experimental_rerun()
