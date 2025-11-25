# backend_core/dashboard/views/product_details_pro.py

import streamlit as st
from datetime import datetime

from backend_core.services.product_repository_v2 import (
    get_product_v2,
    get_category_by_id,
    get_provider_by_id,
)


def _choose_label(obj: dict, fallback: str = "—") -> str:
    """
    Intenta devolver un nombre legible para una categoría o proveedor
    probando varias claves típicas, y si no, el id.
    """
    if not obj:
        return fallback

    for key in ("name", "nombre", "label", "title"):
        if key in obj and obj[key]:
            return str(obj[key])

    if "id" in obj and obj["id"]:
        return str(obj["id"])

    return fallback


def _info(label: str, value: str):
    st.markdown(f"**{label}:**<br>{value}", unsafe_allow_html=True)
    st.divider()


def _render_price_block(product):
    st.markdown("### 💶 Precio")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Final", f"{product['price_final']} €")

    with col2:
        base = product.get("price_base")
        st.metric("Base", f"{base} €" if base is not None else "—")

    with col3:
        vat = product.get("vat_rate")
        st.metric("IVA", f"{vat} %" if vat is not None else "—")

    st.divider()


def render_product_details_pro(product_id: str):
    product = get_product_v2(product_id)

    if not product:
        st.error("❌ Producto no encontrado.")
        return

    # HEADER
    st.title(product["name"])

    # IMAGE
    if product.get("image_url"):
        st.image(
            product["image_url"],
            width=450,
            caption=product.get("name", "Producto"),
        )

    st.divider()

    # PRECIO
    _render_price_block(product)

    # INFO
    st.subheader("📄 Información del producto")

    if product.get("description"):
        st.markdown(product["description"])
        st.divider()

    # Proveedor
    provider = get_provider_by_id(product.get("provider_id"))
    provider_name = _choose_label(provider)
    _info("Proveedor", provider_name)

    # Categoría
    category = get_category_by_id(product.get("category_id"))
    category_name = _choose_label(category)
    _info("Categoría", category_name)

    # SKU
    _info("SKU", product.get("sku") or "—")

    # currency
    _info("Moneda", product.get("currency") or "EUR")

    # Active
    _info("Activo", "Sí" if product.get("active") else "No")

    # created_at
    created_raw = product.get("created_at")
    if created_raw:
        try:
            created_fmt = datetime.fromisoformat(
                created_raw.replace("Z", "")
            ).strftime("%Y-%m-%d %H:%M")
        except Exception:
            created_fmt = created_raw
    else:
        created_fmt = "—"

    _info("Creado", created_fmt)

    # JSON RAW
    with st.expander("🔧 Ver JSON RAW (debug)"):
        st.json(product)
