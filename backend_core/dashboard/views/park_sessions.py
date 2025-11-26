# backend_core/dashboard/views/park_sessions.py

import streamlit as st
from datetime import datetime, timedelta

from backend_core.services.session_repository import (
    create_session,
    activate_session,
    get_parked_sessions,
)
from backend_core.services.product_repository_v2 import (
    list_products_v2,
    get_product_v2,
)
from backend_core.services.module_repository import (
    list_all_modules,
    assign_module,
    get_module_for_session,
)
from backend_core.services.audit_repository import log_event


# ======================================================================
# RENDER PRINCIPAL
# ======================================================================
def render_park_sessions():
    st.title("📦 Parked Sessions")

    # Se requiere operador logueado
    operator_id = st.session_state.get("operator_id")
    if not operator_id:
        st.error("Debe iniciar sesión como operador.")
        return

    # -------------------------------------------------------------
    # Cargar productos (versión moderna v2)
    # -------------------------------------------------------------
    try:
        products = list_products_v2(operator_id)
    except Exception as e:
        st.error(f"Error cargando productos: {e}")
        return

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
    try:
        modules = list_all_modules(operator_id)
    except Exception:
        modules = []

    module_options = {m["module_code"]: m["id"] for m in modules} if modules else {}

    if not module_options:
        st.error("No hay módulos definidos.")
        return

    selected_module_code = st.selectbox("Módulo", list(module_options.keys()))
    selected_module_id = module_options[selected_module_code]

    # -------------------------------------------------------------
    # Selección de capacity
    # -------------------------------------------------------------
    capacity = st.number_input("Aforo de la sesión", min_value=1, max_value=99999, value=10)

    expires_days = st.number_input("Expira en días", min_value=1, max_value=30, value=5)

    # -------------------------------------------------------------
    # Crear sesión parked
    # -------------------------------------------------------------
    if st.button("Crear sesión parked"):
        try:
            session_id = create_session(
                product_id=selected_product_id,
                module_id=selected_module_id,
                aforo=capacity,
                expires_in_days=expires_days,
                operator_id=operator_id
            )
        except Exception as e:
            st.error(f"Error creando sesión: {e}")
            return

        log_event("session_created_parked", session_id=session_id, operator_id=operator_id)

        st.success(f"Sesión creada: {session_id}")

    st.markdown("---")

    # =================================================================
    # LISTA DE PARKED SESSIONS
    # =================================================================
    st.subheader("Sesiones parked existentes")

    try:
        sessions = get_parked_sessions(operator_id)
    except Exception as e:
        st.error(f"No se han podido cargar las sesiones parked: {e}")
        return

    if not sessions:
        st.info("No hay sesiones parked.")
        return

    for s in sessions:
        st.write(f"### Sesión `{s['id']}`")

        st.write(f"- Aforo: {s.get('aforo')}")
        st.write(f"- Participantes: {s.get('pax_registered', 0)}")
        st.write(f"- Expira: {s.get('expires_at')}")

        # Mostrar nombre del producto
        product = get_product_v2(s["product_id"])
        if product:
            st.write(f"- Producto: **{product['name']}** — {product['price_final']} €")
            if product.get("image_url"):
                st.image(product["image_url"], width=150)

        # Mostrar módulo asignado
        mod = _get_module_for_display(s["id"])
        if mod:
            st.write(f"- Módulo: **{mod.get('module_code')}**")

        # Activar sesión
        if st.button(f"Activar sesión {s['id']}"):
            try:
                activate_session(s["id"], operator_id)
                log_event("session_activated", session_id=s["id"], operator_id=operator_id)
                st.success("Sesión activada correctamente")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error activando sesión: {e}")


# ======================================================================
# Función auxiliar
# ======================================================================
def _get_module_for_display(session_id: str):
    try:
        return get_module_for_session(session_id)
    except Exception:
        return None
