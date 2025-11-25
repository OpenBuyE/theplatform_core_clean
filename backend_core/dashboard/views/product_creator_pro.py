# backend_core/dashboard/views/product_creator_pro.py

import streamlit as st

from backend_core.services.product_repository_v2 import (
    create_product,
    list_categories,
)

from backend_core.services.supabase_client import table

# Tabla real de proveedores
OPERATORS_TABLE = "ca_operators"


# ===========================================================
# Helpers reales
# ===========================================================

def list_providers():
    """
    Lista operadores reales desde ca_operators.
    Campos esperados:
        - id
        - name
        - legal_name
    """
    try:
        resp = (
            table(OPERATORS_TABLE)
            .select("*")
            .order("name")
            .execute()
        )
        return resp.data or []
    except Exception:
        return []


# ===========================================================
# PRODUCT CREATOR PRO
# ===========================================================

def render_product_creator_pro():
    st.title("🛠 Product Creator PRO")

    st.markdown("Crea productos completos para **products_v2**.")

    categories = list_categories()
    providers = list_providers()

    # Campos principales
    name = st.text_input("Nombre del producto")
    sku = st.text_input("SKU (opcional)")

    price_final = st.number_input("Precio final (€)", min_value=0.0, step=0.01)
    price_base = st.number_input("Precio base (€)", min_value=0.0, step=0.01)
    vat_rate = st.number_input("IVA (%)", min_value=0.0, step=1.0, value=21.0)

    currency = st.selectbox("Moneda", ["EUR", "USD", "GBP"])

    description = st.text_area("Descripción", height=100)

    # CATEGORY SELECT
    category_map = {c["categoria"]: c["id"] for c in categories} if categories else {}
    category_name = st.selectbox("Categoría", ["Sin categoría"] + list(category_map.keys()))
    category_id = None if category_name == "Sin categoría" else category_map[category_name]

    # PROVIDER SELECT
    providers_map = {p.get("name", p["id"]): p["id"] for p in providers}
    provider_name = st.selectbox("Proveedor", list(providers_map.keys()))
    provider_id = providers_map[provider_name]

    # Organización fija por ahora
    organization_id = "11111111-1111-1111-1111-111111111111"

    # Imagen
    image_url = st.text_input("URL de imagen (Unsplash u otra)")

    # -------------------------------------
    # BOTÓN DE CREACIÓN
    # -------------------------------------
    if st.button("Crear producto", type="primary"):
        data = {
            "organization_id": organization_id,
            "provider_id": provider_id,
            "sku": sku or None,
            "name": name,
            "description": description or None,
            "price_final": price_final,
            "price_base": price_base,
            "vat_rate": vat_rate,
            "currency": currency,
            "image_url": image_url or None,
            "category_id": category_id,
        }

        ok = create_product(data)

        if ok:
            st.success("Producto creado correctamente 🎉")
            st.balloons()
        else:
            st.error("Error al crear el producto. Revisa los datos o la consola.")
