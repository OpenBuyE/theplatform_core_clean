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
from backend_core.services.module_repository import get_module_by_id


# =======================================================
# VISTA PARKED SESSIONS
# =======================================================

def render_park_sessions():

    st.header("Parked Sessions")

    # =============================
    # 1. Selección de producto
    # =============================
    products = list_products()
    product_map = {p["name"]: p["id"] for p in products}
    product_names = list(product_map.keys())

    if not products:
        st.warning("No hay productos disponibles.")
        return

    selected_product = st.selectbox("Producto", product_names)
    product_id = product_map[selected_product]

    st.write("---")

    # =============================
    # 2. Selección de módulo
    # =============================
    modules = list_all_modules()
    if not modules:
        st.warning("No hay módulos creados.")
        return

    module_options = {
        f"{m['module_code']} — {m['id'][0:8]}": m["id"] for m in modules
    }

    selected_module_label = st.selectbox("Módulo asociado", list(module_options.keys()))
    selected_module_id = module_options[selected_module_label]

    st.write("---")

    # =============================
    # 3. Parámetros de sesión
    # =============================
    capacity = st.number_input("Capacity", value=10, min_value=1)
    expires_in_days = st.number_input("Expiración (días)", value=5, min_value=1)

    st.write("---")

    # =============================
    # 4. Crear sesión parked
    # =============================
    if st.button("Crear sesión PARKED"):

        # Crear serie y sesiones corresponde a module_factory.
        # Aquí solo estamos creando sesiones manuales para debug.
        now = datetime.utcnow()

        # sequence_number fijo para debug (NO producción)
        sequence_number = 1  

        session = create_parked_session(
            product_id=product_id,
            organization_id="00000000-0000-0000-0000-000000000001",
            series_id="DEBUG_SERIES",
            sequence_number=sequence_number,
            capacity=capacity,
            expires_in_days=expires_in_days,
            module_code="A_DETERMINISTIC",
            module_id=selected_module_id,
        )

        log_event("parked_session_created_manual", session_id=session["id"])

        st.success(f"Sesión parked creada: {session['id']}")

    st.write("---")

    # =============================
    # 5. Mostrar parked existentes
    # =============================
    st.subheader("Sesiones PARKED existentes")

    parked = get_parked_sessions()

    if not parked:
        st.info("No hay sesiones parked.")
        return

    for s in parked:
        st.write(f"### Sesión {s['id']}")
        st.write(f"- Estado: {s['status']}")
        st.write(f"- Aforo: {s['pax_registered']} / {s['capacity']}")
        st.write(f"- Expira: {s['expires_at']}")

        # Mostrar módulo
        if s.get("module_id"):
            mod = get_module_by_id(s["module_id"])
            if mod:
                st.write(f"- Módulo: **{mod['module_code']}** — {mod['id']}")

        # Mostrar producto
        product = get_product(s["product_id"])
        if product:
            st.write(f"- Producto: **{product['name']}** – {product['price']}€")

        st.write("---")
