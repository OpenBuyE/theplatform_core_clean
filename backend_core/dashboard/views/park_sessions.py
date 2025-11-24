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
from backend_core.services.module_repository import list_modules, assign_module_to_session


# =======================================================
# CREAR SESIÓN PARKED
# =======================================================

def render_park_sessions():

    st.header("📦 Parked Sessions (Crear / Gestionar)")

    st.subheader("Crear nueva sesión")

    # -------------------------------------------------------
    # LISTA PRODUCTOS
    # -------------------------------------------------------
    products = list_products()
    product_dict = {p["id"]: p for p in products}
    product_names = {f"{p['name']} — {p['price']}€": p["id"] for p in products}

    selected_product_label = st.selectbox(
        "Producto:",
        options=list(product_names.keys()) if product_names else ["No hay productos"],
    )

    selected_product_id = product_names.get(selected_product_label)

    # -------------------------------------------------------
    # SELECTOR DE MÓDULO
    # -------------------------------------------------------

    st.subheader("Módulo de Sesión")

    modules = list_modules()
    modules_map = {f"{m['module_code']} — {m['name']}": m["module_code"] for m in modules}

    selected_module_label = st.selectbox(
        "Selecciona un módulo:",
        options=list(modules_map.keys()),
    )

    selected_module_code = modules_map[selected_module_label]

    # -------------------------------------------------------
    # OTROS CAMPOS
    # -------------------------------------------------------

    organization_id = st.text_input(
        "Organization ID:",
        placeholder="UUID de operador",
    )

    capacity = st.number_input(
        "Aforo", min_value=1, step=1, value=10
    )

    expires_in_days = st.number_input(
        "Expira en días (5 por defecto):",
        min_value=1, step=1, value=5
    )

    expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    # -------------------------------------------------------
    # CREAR SESIÓN
    # -------------------------------------------------------

    if st.button("Crear sesión PARKED"):
        if not organization_id or not selected_product_id:
            st.error("Organization ID y producto son obligatorios.")
            return

        session = create_parked_session(
            product_id=selected_product_id,
            organization_id=organization_id,
            capacity=capacity,
            expires_at=expires_at,
        )

        # Asignar módulo
        assign_module_to_session(session["id"], selected_module_code)

        log_event(
            action="session_created_parked",
            session_id=session["id"],
            user_id=None,
            metadata={"module": selected_module_code},
        )

        st.success(f"Sesión creada correctamente (ID: {session['id']})")

    st.markdown("---")

    # =======================================================
    # LISTAR SESIONES PARKED
    # =======================================================

    st.subheader("Sesiones Parked existentes")

    sessions = get_parked_sessions()

    for s in sessions:
        st.write(f"### Sesión: {s['id']}")
        st.write(f"- Producto: {s['product_id']}")
        st.write(f"- Organization: {s['organization_id']}")
        st.write(f"- Aforo: {s['capacity']}")
        st.write(f"- Pax Registered: {s['pax_registered']}")
        st.write(f"- Expira: {s['expires_at']}")
        st.write(f"- Módulo: **{s.get('module_code', 'A_DETERMINISTIC')}**")

        product = get_product(s["product_id"])
        if product:
            st.write(f"- Producto: **{product['name']}** — {product['price']}€")
            if product.get("image_url"):
                st.image(product["image_url"], width=200)

        # Activar sesión
        if st.button(f"Activar sesión {s['id']}"):
            activate_session(s["id"])
            st.success("Sesión activada correctamente")
