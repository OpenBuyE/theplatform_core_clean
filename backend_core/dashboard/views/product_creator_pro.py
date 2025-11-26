# backend_core/dashboard/views/product_creator_pro.py
# =======================================================
# PRODUCT CREATOR PRO — Alta Profesional de Productos
# =======================================================

import streamlit as st
from datetime import datetime

from backend_core.services.product_repository_v2 import (
    create_product,
    list_categories,
)

from backend_core.services.provider_repository_v2 import (
    list_providers_safe,
)


# =======================================================
# MAIN RENDER FUNCTION
# =======================================================
def render_product_creator_pro():
    st.title("🛒 Product Creator Pro")
    st.write("Alta profesional de productos en **products_v2**")

    st.markdown("---")

    # =======================================================
    # LOAD SUPPORTING DATA
    # =======================================================
    categories = list_categories()
    providers = list_providers_safe()

    # CATEGORY MAP
    category_map = {c["nombre"]: c["id"] for c in categories} if categories else {}

    # PROVIDER MAP
    provider_map = {p["name"]: p["id"] for p in providers} if providers else {}

    # =======================================================
    # FORM
    # =======================================================
    with st.form("product_creator_form"):
        st.subheader("Información del producto")

        name = st.text_input("Nombre del producto *")
        sku = st.text_input("SKU")
        description = st.text_area("Descripción", height=120)

        price_final = st.number_input("Precio Final (€)", min_value=0.0, format="%.2f")
        price_base = st.number_input("Precio Base (€)", min_value=0.0, format="%.2f")
        vat_rate = st.number_input("IVA (%)", min_value=0.0, format="%.2f", value=21.0)

        image_url = st.text_input("URL de imagen")

        st.markdown("### Categoría")
        category_name = st.selectbox(
            "Categoría",
            ["Sin categoría"] + list(category_map.keys())
        )
        category_id = None if category_name == "Sin categoría" else category_map[category_name]

        st.markdown("### Proveedor")
        provider_name = st.selectbox(
            "Proveedor",
            ["Sin proveedor"] + list(provider_map.keys())
        )
        provider_id = None if provider_name == "Sin proveedor" else provider_map[provider_name]

        st.markdown("---")

        submitted = st.form_submit_button("Crear Producto", type="primary")

    # =======================================================
    # PROCESS FORM
    # =======================================================
    if submitted:
        if not name:
            st.error("El nombre del producto es obligatorio.")
            return

        if not provider_id:
            st.error("Debes seleccionar un proveedor válido.")
            return

        if price_final <= 0:
            st.error("El precio final debe ser mayor que 0.")
            return

        data = {
            "name": name,
            "sku": sku,
            "description": description,
            "price_final": price_final,
            "price_base": price_base,
            "vat_rate": vat_rate,
            "currency": "EUR",
            "image_url": image_url,
            "provider_id": provider_id,
            "category_id": category_id,
            "organization_id": "11111111-1111-1111-1111-111111111111",
            "created_at": datetime.utcnow().isoformat()
        }

        try:
            create_product(data)
            st.success("Producto creado correctamente.")
            st.balloons()
        except Exception as e:
            st.error(f"Error al crear el producto: {str(e)}")
