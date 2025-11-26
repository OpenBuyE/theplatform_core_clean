# backend_core/dashboard/views/product_creator_pro.py

import streamlit as st
from datetime import datetime

from backend_core.services.product_repository_v2 import (
    create_product,
    list_categories,
    list_providers_safe,
)

# ===========================================================
# PRODUCT CREATOR PRO
# ===========================================================

def render_product_creator_pro():
    st.title("🛠️ Product Creator Pro")
    st.write("Crear un nuevo producto en products_v2")

    # -------------------------------------------------------
    # CATEGORIES
    # -------------------------------------------------------
    categories = list_categories()
    category_map = {c["nombre"]: c["id"] for c in categories} if categories else {}
    category_name = st.selectbox(
        "Categoría",
        ["Sin categoría"] + list(category_map.keys())
    )
    category_id = None if category_name == "Sin categoría" else category_map[category_name]

    # -------------------------------------------------------
    # PROVIDERS
    # -------------------------------------------------------
    providers = list_providers_safe()
    provider_map = {p["name"]: p["id"] for p in providers} if providers else {}
    provider_name = st.selectbox(
        "Proveedor",
        list(provider_map.keys()) if provider_map else ["Sin proveedores"]
    )
    provider_id = provider_map.get(provider_name)

    st.write("---")

    # -------------------------------------------------------
    # PRODUCT DATA
    # -------------------------------------------------------
    name = st.text_input("Nombre del producto")
    sku = st.text_input("SKU")
    description = st.text_area("Descripción", height=100)
    price_final = st.number_input("Precio final (€)", min_value=0.00, format="%.2f")
    price_base = st.number_input("Precio base (€)", min_value=0.00, format="%.2f")
    vat_rate = st.number_input("IVA (%)", min_value=0.00, format="%.2f")
    currency = "EUR"
    image_url = st.text_input("Imagen URL (opcional)")

    st.write("---")

    # -------------------------------------------------------
    # SAVE BUTTON
    # -------------------------------------------------------
    if st.button("💾 Crear producto"):
        if not name or not provider_id:
            st.error("El nombre y el proveedor son obligatorios.")
            return
        
        ok = create_product(
            organization_id="11111111-1111-1111-1111-111111111111",
            provider_id=provider_id,
            sku=sku,
            name=name,
            description=description,
            price_final=price_final,
            price_base=price_base,
            vat_rate=vat_rate,
            currency=currency,
            image_url=image_url,
            category_id=category_id
        )

        if ok:
            st.success("Producto creado correctamente en products_v2.")
        else:
            st.error("Error al crear el producto. Revisa los logs.")
