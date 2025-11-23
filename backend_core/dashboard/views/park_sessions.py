# backend_core/dashboard/views/park_sessions.py

import streamlit as st

from backend_core.services.session_repository import (
    create_parked_session,
    activate_session,
    get_parked_sessions,
)

from backend_core.services.product_repository import list_products, get_product
from backend_core.services.audit_repository import AuditRepository


audit = AuditRepository()


def render_park_sessions():
    st.title("Parked Sessions")
    st.write("Crear y gestionar sesiones en estado 'parked' con productos reales.")

    st.subheader("Crear nueva sesión parked")

    # --------------------------------------------------------
    # Cargar productos para dropdown
    # --------------------------------------------------------
    st.write("### Selección de producto")

    organization_id = st.text_input(
        "Organization ID (para cargar productos)",
        placeholder="uuid-organización",
        key="org_products_input",
    )

    if organization_id:
        products = list_products(organization_id)
    else:
        products = []

    product_map = {
        f"{p['name']} — {p['price_final']}€ (SKU: {p.get('sku','')})": p["id"]
        for p in products
    }

    if products:
        product_label = st.selectbox(
            "Selecciona un producto",
            list(product_map.keys()),
            help="Productos reales desde products_v2",
        )

        selected_product_id = product_map[product_label]
        selected_product = get_product(selected_product_id)

        # Vista previa del producto
        st.write("### Vista previa del producto seleccionado:")
        st.json(selected_product)

    else:
        selected_product_id = None
        st.info("Introduce Organization ID para cargar productos.")
        selected_product = None

    # --------------------------------------------------------
    # CREAR SESIÓN
    # --------------------------------------------------------

    st.write("### Crear sesión parked")

    with st.form("create_session_form"):
        series_id = st.text_input("Series ID", placeholder="uuid-serie")

        capacity = st.number_input(
            "Capacity (aforo)",
            min_value=1,
            step=1,
            help="Número de participantes necesarios para completar la sesión"
        )

        submit_create = st.form_submit_button("Crear sesión parked")

        if submit_create:
            if not organization_id or not series_id or not selected_product_id:
                st.error("Todos los campos son obligatorios, incluyendo el producto.")
            else:
                session = create_parked_session(
                    series_id=series_id,
                    product_id=selected_product_id,
                    organization_id=organization_id,
                    capacity=capacity,
                )
                audit.log(
                    action="SESSION_CREATED_PARKED",
                    session_id=session["id"],
                    metadata={"product_id": selected_product_id},
                )
                st.success(f"Sesión creada correctamente: {session['id']}")

    st.divider()

    # --------------------------------------------------------
    # SESIONES PARKED EXISTENTES
    # --------------------------------------------------------

    st.subheader("Sesiones parked existentes")

    sessions = get_parked_sessions()
    if not sessions:
        st.info("No hay sesiones parked.")
        return

    for s in sessions:
        st.write(f"📦 **Sesión:** {s['id']}")
        st.write(f"- Organization: {s['organization_id']}")
        st.write(f"- Series ID: {s['series_id']}")
        st.write(f"- Capacity: {s['capacity']}")
        st.write(f"- Pax Registered: {s['pax_registered']}")

        # Mostrar nombre del producto
        product = get_product(s["product_id"])
        if product:
            st.write(f"- Producto: **{product['name']}** — {product['price_final']}€")
            if product.get("image_url"):
                st.image(product["image_url"], width=200)

        st.write("---")

        if st.button(f"Activar sesión {s['id']}", key=f"activate_{s['id']}"):
            activate_session(s["id"])
            audit.log(
                action="SESSION_ACTIVATED_FROM_UI",
                session_id=s["id"],
                metadata={},
            )
            st.success(f"Sesión activada: {s['id']}")
            st.experimental_rerun()
