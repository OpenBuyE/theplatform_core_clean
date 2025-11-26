import streamlit as st
from backend_core.services.product_repository_v2 import (
    list_products_v2,
    filter_products,
    list_categories,
    list_providers_v2,
)

def render_product_catalog_pro():
    st.title("📦 Catálogo de Productos")

    # ================================
    # Sidebar de Categorías
    # ================================
    categories = list_categories()

    # Las categorías vienen con campo "nombre"
    category_names = ["Todas"] + [c["nombre"] for c in categories]

    selected_cat_name = st.selectbox("Categoría", category_names)

    # Obtener category_id si no es “Todas”
    if selected_cat_name == "Todas":
        selected_category_id = None
    else:
        selected_category_id = next(
            (c["id"] for c in categories if c["nombre"] == selected_cat_name),
            None,
        )

    # ================================
    # Sidebar de Proveedores
    # ================================
    providers = list_providers_v2()
    provider_names = ["Todos"] + [p["name"] for p in providers]

    selected_prov_name = st.selectbox("Proveedor", provider_names)

    if selected_prov_name == "Todos":
        selected_provider_id = None
    else:
        selected_provider_id = next(
            (p["id"] for p in providers if p["name"] == selected_prov_name),
            None,
        )

    # ================================
    # Cargar productos filtrados
    # ================================
    products = filter_products(
        category_id=selected_category_id,
        provider_id=selected_provider_id,
    )

    st.write(f"### Resultados: {len(products)} productos encontrados")

    # ================================
    # Render Cards
    # ================================
    cols = st.columns(3)

    for idx, product in enumerate(products):
        col = cols[idx % 3]
        with col:
            st.image(product.get("image_url"), use_column_width=True)
            st.subheader(product.get("name"))
            st.write(f"SKU: {product.get('sku')}")
            st.write(f"Precio: {product.get('price_final')} {product.get('currency')}")
            st.write(f"Categoría: {product.get('category_id')}")
            st.write(f"Proveedor: {product.get('provider_id')}")
            if st.button("Ver Ficha", key=f"view_{product['id']}"):
                st.session_state["product_details_id"] = product["id"]
                st.experimental_rerun()
