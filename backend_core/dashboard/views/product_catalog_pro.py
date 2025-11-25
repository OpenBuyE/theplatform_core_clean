# backend_core/dashboard/views/product_catalog_pro.py

import streamlit as st
import math

from backend_core.services.product_repository_v2 import (
    list_products,
    list_categories,
    filter_products,
)

# ---------------------------
#   CARD COMPONENT
# ---------------------------
def product_card(prod):
    st.markdown(
        f"""
        <div style="
            border:1px solid #E6EAF0;
            border-radius:12px;
            padding:16px;
            background:white;
            box-shadow:0 1px 2px rgba(0,0,0,0.04);
        ">
            <img src="{prod.get('image_url', '')}" 
                 style="width:100%; border-radius:8px;"/>
            <h4 style="margin-top:12px;">{prod['name']}</h4>
            <p style="color:#5A6A80; font-size:14px;">
                {prod.get('description', '')}
            </p>
            <b style="font-size:18px; color:#1747FF;">
                {prod['price_final']} €
            </b><br>
            <span style="color:#7A8899; font-size:12px;">
                SKU: {prod['sku']}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )


# ---------------------------
# MAIN
# ---------------------------
def render_product_catalog_pro():
    st.title("🛍️ Product Catalog PRO")
    st.caption("Vista avanzada del catálogo corporativo")

    # -------------------------------------
    # FILTER BAR
    # -------------------------------------
    st.subheader("🔍 Filtros")

    categories = list_categories()
    category_options = {c["name"]: c["id"] for c in categories} if categories else {}

    col1, col2 = st.columns(2)
    with col1:
        selected_category = st.selectbox("Categoría", ["Todas"] + list(category_options.keys()))
    with col2:
        filter_active = st.selectbox("Disponibilidad", ["Todos", "Activos", "Inactivos"])

    col3, col4 = st.columns(2)
    with col3:
        min_price = st.number_input("Precio mínimo", min_value=0.0, value=0.0)
    with col4:
        max_price = st.number_input("Precio máximo", min_value=0.0, value=0.0)

    # Translate filters
    category_filter = None
    if selected_category != "Todas":
        category_filter = category_options[selected_category]

    active_filter = None
    if filter_active == "Activos":
        active_filter = True
    elif filter_active == "Inactivos":
        active_filter = False

    # -------------------------------------
    # FETCH PRODUCTS
    # -------------------------------------
    products = filter_products(
        category=category_filter,
        active=active_filter,
        min_price=min_price if min_price > 0 else None,
        max_price=max_price if max_price > 0 else None,
    )

    st.write(f"**{len(products)} productos encontrados**")

    # -------------------------------------
    # GRID VIEW
    # -------------------------------------
    st.subheader("📦 Resultados")

    if not products:
        st.info("No se encontraron productos con los filtros aplicados.")
        return

    cols_per_row = 3
    rows = math.ceil(len(products) / cols_per_row)

    for i in range(rows):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = i * cols_per_row + j
            if idx < len(products):
                with cols[j]:
                    product_card(products[idx])
