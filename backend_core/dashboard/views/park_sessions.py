# backend_core/dashboard/views/park_sessions.py

import streamlit as st
from datetime import datetime, timedelta

from backend_core.services.session_repository import (
    create_parked_session,
    activate_session,
    get_parked_sessions,
)
from backend_core.services.audit_repository import log_event
from backend_core.services.product_repository import (
    list_products,
    get_product,
)
from backend_core.services.module_repository import (
    list_all_modules,
    assign_module,
)


# =======================================================
# PARKED SESSIONS VIEW
# =======================================================

def render_park_sessions():
    st.header("Parked Sessions")

    # -------------------------------------------------------
    # FORM: CREATE NEW PARKED SESSION
    # -------------------------------------------------------
    st.subheader("Crear nueva sesión aparcada")

    products = list_products()
    modules = list_all_modules()

    # PRODUCT DROPDOWN
    product_options = {p["name"]: p["id"] for p in products} if products else {}

    selected_product_name = st.selectbox("Producto", list(product_options.keys()))
    selected_product_id = product_options[selected_product_name]

    # MODULE DROPDOWN
    module_options = {m["module_code"]: m["id"] for m in modules} if modules else {}

    selected_module_code = st.selectbox("Módulo", list(module_options.keys()))
    selected_module_id = module_options[selected_module_code]

    capacity = st.number_input("Capacidad", min_value=1, max_value=500, value=10)

    if st.button("Crear sesión aparcada"):
        session = create_parked_session(
            product_id=selected_product_id,
            capacity=capacity,
        )

        # Asignar módulo automáticamente
        assign_module(session["id"], selected_module_id)

        log_event(
            "parked_session_created",
            session_id=session["id"],
            metadata={"product_id": selected_product_id, "module_id": selected_module_id},
        )

        st.success(f"Sesión creada con ID {session['id']} y módulo asignado.")

    st.write("----")

    # -------------------------------------------------------
    # LISTA DE SESIONES APARCADAS
    # -------------------------------------------------------
    st.subheader("Sesiones aparcadas")

    parked = get_parked_sessions()
    if not parked:
        st.info("No hay sesiones aparcadas.")
        return

    for s in parked:
        st.write("----")
        st.write(f"**Session ID:** {s['id']}")
        st.write(f"Capacidad: {s['capacity']}")
        st.write(f"Pax registrados: {s['pax_registered']}")

        # Producto
        product = get_product(s["product_id"])
        if product:
            st.write(f"Producto: **{product['name']}** — {product['price']}€")

            if product.get("image_url"):
                st.image(product["image_url"], width=150)

        # Módulo asignado
        st.write(f"Módulo asignado: {s.get('module_id', 'N/A')}")

        # ACTIVAR
        if st.button(f"Activar sesión {s['id']}"):
            activate_session(s["id"])
            st.success(f"Sesión {s['id']} activada.")
