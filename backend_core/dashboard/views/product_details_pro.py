# backend_core/dashboard/views/product_details_pro.py

import streamlit as st
from datetime import datetime

from backend_core.services.product_repository_v2 import (
    get_product_v2,
    get_category_by_id,
    get_provider_by_id,
)


# =====================================================
# HELPER — Renderizar Bloque de Info
# =====================================================
def _info(label: str, value: str):
    st.markdown(f"**{label}:**<br>{value}", unsafe_allow_html=True)
    st.divider()


# =====================================================
# HELPER — Caja de precio estilo fintech
# =====================================================
def _render_price_block(product):
    st.markdown("### 💶 Precio")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Final", f"{product['price_final']} €")

    with col2:
        if product.get("price_base"):
            st.metric("Base", f"{product['price_base']} €")
        else:
            st.metric("Base", "—")

    with col3:
        if product.get("vat_rate"):
            st.metric("IVA", f"{product['vat_rate']} %")
        else:
            st.metric("IVA", "—")

    st.divider()


# =====================================================
# MAIN RENDER
# =====================================================
def render_product_details_pro(product_id: str):

    product = get_product_v2(product_id)

    if not product:
        st.error("❌ Producto no encontrado.")
        return

    # -------- HEADER --------
    st.title(product["name"])

    # -------- IMAGE --------
    st.image(
        product.get("image_url", ""),
        width=450,
        caption=product.get("name", "Producto")
    )

    st.divider()

    # -------- PRICE --------
    _render_price_block(product)

    # -------- INFO --------
    st.subheader("📄 Información del producto")

    # descripción
    if product.get("description"):
        st.markdown(product["description"])
        st.divider()

    # provider
    provider = get_provider_by_id(product.get("provider_id"))
    provider_name = provider["name"] if provider else "—"
    _info("Proveedor", provider_name)

    # categoría
    category = get_category_by_id(product.get("category_id"))
    category_name = category["name"] if category else "—"
    _info("Categoría", category_name)

    # SKU
    _info("SKU", product.get("sku") or "—")

    # currency
    _info("Moneda", product.get("currency") or "EUR")

    # Active
    _info("Activo", "Sí" if product.get("active") else "No")

    # created_at
    created_raw = product.get("created_at")
    try:
        created_fmt = datetime.fromisoformat(created_raw.replace("Z", "")).strftime("%Y-%m-%d %H:%M")
    except:
        created_fmt = created_raw or "—"

    _info("Creado", created_fmt)

    # -------- ADVANCED --------
    with st.expander("🔧 Ver JSON RAW (debug)"):
        st.json(product)
