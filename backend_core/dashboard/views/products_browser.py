# backend_core/dashboard/views/products_browser.py

import streamlit as st

from backend_core.services.product_repository import list_products


def render_products_browser():
    st.title("📦 Products Browser")

    st.write("Explora los productos cargados en `products_v2`.")

    col_filters = st.columns([2, 1])
    search_text = col_filters[0].text_input("Buscar por nombre o SKU", "")
    only_active = col_filters[1].checkbox("Solo activos", value=True)

    products = list_products(only_active=only_active)

    # Filtro simple en memoria
    if search_text:
        s = search_text.lower()
        products = [
            p
            for p in products
            if s in (p.get("name") or "").lower()
            or s in (p.get("sku") or "").lower()
        ]

    count = len(products)
    st.caption(f"{count} productos encontrados.")

    if not products:
        st.warning("No hay productos para mostrar. Usa Admin Seeds → Seed Products V2.")
        return

    # Vista tipo cards en grid
    cols = st.columns(3)

    for idx, p in enumerate(products):
        col = cols[idx % 3]
        with col:
            st.markdown(
                f"""
                <div style="
                    background-color:white;
                    border-radius:12px;
                    padding:16px;
                    margin-bottom:16px;
                    border:1px solid #e5e7eb;
                    box-shadow:0 1px 2px rgba(0,0,0,0.03);
                ">
                    <div style="font-size:13px;color:#6b7280;">{p.get('sku','')}</div>
                    <div style="font-size:16px;font-weight:600;margin-top:4px;">
                        {p.get('name','')}
                    </div>
                    <div style="font-size:13px;color:#6b7280;margin-top:4px;">
                        {p.get('description','')[:80]}...
                    </div>
                    <div style="font-size:15px;font-weight:700;color:#2563eb;margin-top:8px;">
                        {p.get('price_final','')} {p.get('currency','EUR')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if p.get("image_url"):
                st.image(p["image_url"], use_column_width=True)
