# backend_core/dashboard/views/product_creator_pro.py

import streamlit as st
from uuid import uuid4
from datetime import datetime

from backend_core.services.product_repository_v2 import (
    create_product,
    list_categories,
)

# Si tienes providers:
from backend_core.services.providers_seeder import list_providers_safe


# ===========================================================
# UI PRINCIPAL
# ===========================================================

def render_product_creator_pro():
    st.title("🛠 Product Creator PRO")
    st.caption("Crea productos profesionales en products_v2")

    st.markdown("---")

    # =============================
    # Cargar datos auxiliares
    # =============================
    categories = list_categories()
    providers = list_providers_safe() if _providers_enabled() else []

    # Mapas para dropdown
    category_map = {c["name"]: c["id"] for c in categories}
    provider_map = {p["name"]: p["id"] for p in providers}

    # =============================
    # FORM PRINCIPAL
    # =============================
    with st.form("create_product_form"):
        st.subheader("📦 Datos del Producto")

        name = st.text_input("Nombre del producto", max_chars=120)

        sku = st.text_input("SKU / referencia interna", max_chars=80)

        description = st.text_area(
            "Descripción",
            placeholder="Descripción breve del producto",
            height=100,
        )

        price_final = st.number_input("Precio final (€)", min_value=0.00, step=0.10)
        price_base = st.number_input("Precio base (€)", min_value=0.00, step=0.10)
        vat_rate = st.number_input(
            "IVA (%)", min_value=0.0, max_value=100.0, step=0.5
        )

        # Categoría
        st.subheader("📂 Categoría")
        category_name = st.selectbox(
            "Selecciona categoría",
            list(category_map.keys()),
        )
        category_id = category_map[category_name]

        # Proveedor opcional
        st.subheader("🏭 Proveedor (opcional)")
        if providers:
            provider_name = st.selectbox(
                "Proveedor",
                list(provider_map.keys()),
                help="Proveedor asociado al producto",
            )
            provider_id = provider_map[provider_name]
        else:
            provider_id = None
            st.info("No hay proveedores cargados.")

        st.subheader("🖼 Imagen del producto")
        image_url = st.text_input(
            "URL de imagen",
            placeholder="https://source.unsplash.com/featured/?product"
        )

        # Botón enviar
        submitted = st.form_submit_button("➕ Crear Producto")

    # ==============================================
    # SUBMISIÓN DEL FORMULARIO
    # ==============================================
    if submitted:
        if not name:
            st.error("El producto debe tener nombre.")
            return

        new_id = str(uuid4())

        payload = {
            "id": new_id,
            "organization_id": "11111111-1111-1111-1111-111111111111",
            "provider_id": provider_id,
            "category_id": category_id,
            "sku": sku,
            "name": name,
            "description": description,
            "price_final": price_final,
            "price_base": price_base,
            "vat_rate": vat_rate,
            "currency": "EUR",
            "image_url": image_url,
        }

        ok = create_product(payload)

        if ok:
            st.success(f"Producto creado correctamente ✔\nID: {new_id}")
            st.balloons()
        else:
            st.error("Error creando el producto en Supabase.")


# ===========================================
# UTILIDADES
# ===========================================

def _providers_enabled() -> bool:
    """Devuelve True si existe provider_seeder con list_providers_safe."""
    try:
        _ = list_providers_safe()
        return True
    except:
        return False
