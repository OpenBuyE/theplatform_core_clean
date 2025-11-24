# backend_core/dashboard/views/admin_seeds.py
import streamlit as st

from backend_core.services.product_seeder import seed_products_v2
from backend_core.services.audit_repository import log_event


# ======================================================
#  ADMIN SEEDS — MODO SEGURO (solo products_v2)
# ======================================================

def render_admin_seeds():
    st.header("🔧 Admin Seeds — Safe Mode")

    st.markdown(
        """
        Esta sección permite ejecutar tareas de inicialización.
        Actualmente está en **modo seguro**, con solo un seeder activo:

        - 🟦 **Seed Products V2**

        El resto de seeders PRO se añadirán más adelante.
        """
    )

    st.divider()

    # --------------------------------------------------
    # Seed Products V2
    # --------------------------------------------------
    st.subheader("📦 Seed Products V2")

    st.write(
        "Genera un conjunto de productos ficticios para pruebas en el dashboard "
        "(20 productos realistas con imágenes, categorías y precios)."
    )

    if st.button("🚀 Ejecutar Seed Products V2"):
        try:
            count = seed_products_v2()
            log_event(
                event_type="admin_seed",
                description=f"Seed Products V2 ejecutado: {count} productos creados."
            )

            st.success(f"✔ Seed completado: {count} productos insertados en products_v2.")

        except Exception as e:
            st.error(f"❌ Error ejecutando seed: {e}")

    st.divider()

    st.info("Modo seguro activado: Seeders avanzados serán añadidos más adelante.")
