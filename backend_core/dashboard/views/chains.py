# backend_core/dashboard/views/chains.py

import streamlit as st

from backend_core.services import supabase_client
from backend_core.services.product_repository import get_product


def render_chains():
    st.title("Chains (Series de sesiones)")
    st.write("Visualiza las series de sesiones y sus productos reales.")

    # ----------------------------------------------------
    # Cargar series (ca_session_series)
    # ----------------------------------------------------
    series_resp = (
        supabase_client.table("ca_session_series")
        .select("*")
        .order("created_at")
        .execute()
    )
    series_list = series_resp.data or []

    if not series_list:
        st.info("No hay series de sesiones.")
        return

    for series in series_list:
        st.subheader(f"🧬 Serie: {series['id']}")
        st.write(f"Organization: {series['organization_id']}")
        st.write(f"Product ID: {series['product_id']}")
        st.write(f"Created at: {series['created_at']}")
        st.write("---")

        # ----------------------------------------------------
        # PRODUCTO
        # ----------------------------------------------------
        product = get_product(series["product_id"])
        st.write("### 🛒 Producto de la serie")

        if product:
            st.write(f"**{product['name']}** — {product['price_final']} €")
            if product.get("sku"):
                st.write(f"SKU: {product['sku']}")
            if product.get("image_url"):
                st.image(product["image_url"], width=220)
        else:
            st.warning("Producto no encontrado en products_v2")

        # ----------------------------------------------------
        # Sesiones de la serie
        # ----------------------------------------------------
        st.write("### 📦 Sesiones de esta serie")

        sessions_resp = (
            supabase_client.table("ca_sessions")
            .select("*")
            .eq("series_id", series["id"])
            .order("created_at")
            .execute()
        )
        sessions = sessions_resp.data or []

        if sessions:
            st.json(sessions)
        else:
            st.info("No hay sesiones asociadas a esta serie.")

        st.divider()
