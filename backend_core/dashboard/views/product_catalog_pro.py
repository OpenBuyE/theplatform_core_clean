# backend_core/dashboard/views/product_catalog_pro.py

import streamlit as st
import math

from backend_core.services.product_repository_v2 import (
    list_products_v2,
    list_categories,
    filter_products,
)

# ==========================================================
#   PRODUCT CATALOG PRO
# ==========================================================
def render_product_catalog_pro():
    st.title("📦 Catálogo Profesional de Productos")

    # ================================
    #  Sidebar de Categorías
    # ================================
    categories = list_categories()
    category_names = ["Todas"] + [c["name"] for c in categories]

    selected_cat_name = st.selectbox("Categoría", category_names)

    if selected_cat_name == "Todas":
        products = list_products_v2()
    else:
        selected = next(c for c in categories if c["name"] == selected_cat_name)
        products = filter_products(selected["id"])

    if not products:
        st.info("No hay productos disponibles en esta categoría.")
        return

    # =======================================
    #  GRID DE PRODUCTOS (4 columnas)
    # =======================================
    cols_per_row = 4
    num_rows = math.ceil(len(products) / cols_per_row)

    for row in range(num_rows):
        cols = st.columns(cols_per_row)

        for col_idx in range(cols_per_row):
            idx = row * cols_per_row + col_idx
            if idx >= len(products):
                break

            p = products[idx]

            with cols[col_idx]:
                st.image(
                    p.get("image_url", "https://via.placeholder.com/300"),
                    use_column_width=True,
                )
                st.markdown(f"### {p['name']}")

                st.write(f"💶 Precio: **{p['price_final']} {p.get('currency','EUR')}**")

                # Botón abrir ficha
                if st.button("🔍 Ver ficha", key=f"view_{p['id']}"):
                    st.session_state["product_view_id"] = p["id"]
                    st.session_state["navigate_to"] = "Product Details Pro"
                    st.rerun()
