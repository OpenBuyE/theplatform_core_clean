# backend_core/dashboard/views/product_catalog_pro.py

import streamlit as st
import math

from backend_core.services.product_repository_v2 import (
    list_products_v2,
    list_categories,
    list_products_by_category,
)


# ---------------------------------------------------------
# HELPER — GRID DE PRODUCTOS
# ---------------------------------------------------------
def _render_product_grid(products):
    if not products:
        st.info("No hay productos disponibles.")
        return

    cols_per_row = 3
    rows = math.ceil(len(products) / cols_per_row)

    for i in range(rows):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = i * cols_per_row + j
            if idx < len(products):
                p = products[idx]
                with cols[j]:
                    st.image(
                        p.get("image_url", ""),
                        width=180,
                    )
                    st.markdown(f"### {p['name']}")
                    st.write(f"**{p['price_final']} €**")
                    st.caption(p.get("description") or "")
                    st.divider()


# ---------------------------------------------------------
# RENDER PRINCIPAL
# ---------------------------------------------------------
def render_product_catalog_pro():

    st.title("📦 Product Catalog — PRO")

    # Cargar categorías
    categories = list_categories()

    category_map = {c.get("id"): c for c in categories}

    # Selector de categoría
    st.subheader("Categorías")
    options = ["Todas"]
    options += [c.get("id") for c in categories]

    choice = st.selectbox("Filtrar por categoría:", options)

    # Productos según categoría
    if choice == "Todas":
        products = list_products_v2()
    else:
        products = list_products_by_category(choice)

    st.write(f"Total productos: **{len(products)}**")

    st.divider()

    # GRID
    _render_product_grid(products)
