# backend_core/dashboard/views/park_sessions.py

import streamlit as st
from datetime import datetime, timedelta

from backend_core.services.session_repository import (
    create_parked_session,
    activate_session,
    get_parked_sessions,
)
from backend_core.services.audit_repository import log_event
from backend_core.services.product_repository import list_products, get_product
from backend_core.services.module_repository import (
    list_all_modules,
    assign_module_to_session,
)


# ======================================================================
# RENDER PRINCIPAL
# ======================================================================
def render_park_sessions():
    st.title("📦 Parked Sessions")

    # -------------------------------------------------------------
    # Cargar productos
    # -------------------------------------------------------------
    products = list_products()
    product_options = {p["name"]: p["id"] for p in products} if products else {}

    st.subheader("Crear nueva sesión parked")

    if not product_options:
        st.error("No hay productos registrados en products_v2.")
        return

    selected_product_name = st.selectbox("Producto", list(product_options.keys()))
    selected_product_id = product_options[selected_product_name]

    # -------------------------------------------------------------
    # Cargar módulos
    # -------------------------------------------------------------
    modules = list_all_modules()
    module_options = {m["module_code"]: m["id"] for m in modules} if modules else {}

    if not module_options:
        st.error("No hay módulos definidos.")
        return

    selected_module_code = st.selectbox("Módulo", list(module_options.keys()))
    selected_module_id = module_options[selected_module_code]

    # -------------------------------------------------------------
    # Selección de capacity
    # -------------------------------------------------------------
    capacity = st.number_input("Capacity", min_value=1, max_value=9999, value=10)

    # -------------------------------------------------------------
    # Crear sesión
    # -------------------------------------------------------------
    if st.button("Crear sesión parked"):
        session_id = create_parked_session(
            product_id=selected_product_id,
            capacity=capacity
        )
        assign_module_to_session(session_id, selected_module_id)

        log_event("session_created_parked", session_id=session_id)

        st.success(f"Sesión creada: {session_id}")

    st.markdown("---")

    # =================================================================
    # LISTA DE PARKED SESSIONS
    # =================================================================
    st.subheader("Sesiones parked existentes")

    sessions = get_parked_sessions()

    if not sessions:
        st.info("No hay sesiones parked.")
        return

    for s in sessions:
        st.write(f"### Sesión {s['id']}")
        st.write(f"- Capacity: {s['capacity']}")
        st.write(f"- Pax Registered: {s['pax_registered']}")

        # Mostrar nombre del producto
        product = get_product(s["product_id"])
        if product:
            st.write(f"- Producto: **{product['name']}** — {product['price']}€")
            if product.get("image_url"):
                st.image(product["image_url"], width=150)

        # Mostrar módulo asignado
        mod = _get_module_for_display(s["id"])
        if mod:
            st.write(f"- Módulo: **{mod['module_code']}** — {mod['name']}")

        # Activar la sesión
        if st.button(f"Activar {s['id']}"):
            activate_session(s["id"])
            log_event("session_activated", session_id=s["id"])
            st.success("Sesión activada")


# ======================================================================
# Función auxiliar
# ======================================================================
from backend_core.services.module_repository import get_module_for_session

def _get_module_for_display(session_id: str):
    try:
        return get_module_for_session(session_id)
    except Exception:
        return None
