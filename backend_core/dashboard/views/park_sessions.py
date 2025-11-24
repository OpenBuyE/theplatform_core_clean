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
    assign_module,
)


# =======================================================
# PARKED SESSIONS VIEW
# =======================================================

def render_park_sessions():
    st.header("Parked Sessions")

    # ---------------------------------------------------
    # LOAD PRODUCTS
    # ---------------------------------------------------
    products = list_products()
    if not products:
        st.warning("No hay productos disponibles en products_v2.")
        return

    product_options = {p["name"]: p["id"] for p in products}

    # Selectbox always needs safe fallback
    selected_product_name = st.selectbox(
        "Producto",
        list(product_options.keys()),
    )

    if not selected_product_name:
        st.info("Selecciona un producto para continuar.")
        return

    selected_product_id = product_options.get(selected_product_name)
    if not selected_product_id:
        st.error("Error interno: product_id no encontrado.")
        return

    # ---------------------------------------------------
    # LOAD MODULES
    # ---------------------------------------------------
    modules = list_all_modules()
    if not modules:
        st.warning("No hay módulos configurados en ca_modules.")
        return

    module_options = {m["module_code"]: m["id"] for m in modules}

    selected_module_code = st.selectbox(
        "Módulo",
        list(module_options.keys()),
    )

    selected_module_id = module_options.get(selected_module_code)
    if not selected_module_id:
        st.error("Error interno: module_id no encontrado.")
        return

    st.write("---")
    st.subheader("Crear nueva sesión parked")

    col1, col2 = st.columns(2)
    with col1:
        capacity = st.number_input("Aforo", min_value=1, max_value=9999, value=10)

    with col2:
        expires_in_days = st.number_input("Expira en (días)", min_value=1, max_value=30, value=5)

    if st.button("Crear sesión parked"):
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        session_id = create_parked_session(
            product_id=selected_product_id,
            capacity=capacity,
            expires_at=expires_at,
        )

        # asigna módulo
        assign_module(session_id, selected_module_id)

        log_event("session_created", {"session_id": session_id})
        st.success(f"Sesión parked creada y módulo asignado. ID: {session_id}")

    st.write("---")
    st.subheader("Sesiones parked existentes")

    parked = get_parked_sessions()

    if not parked:
        st.info("No hay sesiones parked.")
        return

    for s in parked:
        st.write("-----")
        st.write(f"**ID:** {s['id']}")
        st.write(f"Aforo: {s['capacity']}")
        st.write(f"Pax Registered: {s['pax_registered']}")
        st.write(f"Expira: {s['expires_at']}")

        product = get_product(s["product_id"])
        if product:
            st.write(f"- Producto: **{product['name']}** — {product['price']} €")

        if st.button(f"Activar sesión {s['id']}"):
            activate_session(s["id"])
            log_event("session_activated", {"session_id": s["id"]})
            st.success(f"Sesión {s['id']} activada.")
