# backend_core/dashboard/views/admin_seeds.py

import streamlit as st

from backend_core.services.audit_repository import log_event
from backend_core.services.product_seeder import seed_products_v2


def render_admin_seeds():
    st.title("🧪 Admin Seeds")
    st.write("Herramientas internas para poblar datos de desarrollo.")

    st.subheader("📦 Seed Products V2")

    if st.button("Insertar 20 productos fake en products_v2"):
        try:
            inserted = seed_products_v2()
            st.success(f"Éxito: {inserted} productos insertados.")
            log_event("ADMIN_SEEDS", f"Manual seed: {inserted} products inserted.")
        except Exception as e:
            st.error(f"Error al insertar productos: {e}")

    st.info("Los productos solo se insertan si su SKU no existe previamente.")
