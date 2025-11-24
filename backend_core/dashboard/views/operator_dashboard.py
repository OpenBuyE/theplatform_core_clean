# backend_core/dashboard/views/operator_dashboard.py

import streamlit as st

from backend_core.services.supabase_client import table
from backend_core.services.product_repository import get_product
from backend_core.services.module_repository import get_session_module


def _fetch_sessions(organization_id: str, status: str):
    resp = (
        table("ca_sessions")
        .select("*")
        .eq("organization_id", organization_id)
        .eq("status", status)
        .order("activated_at" if status == "active" else "created_at", desc=True)
        .execute()
    )
    return resp.data or []


def render_operator_dashboard():
    st.header("🧩 Operator Dashboard")

    organization_id = st.text_input("Organization ID:")
    if not organization_id:
        st.info("Introduce un Organization ID.")
        return

    st.markdown("## 🔵 Sesiones Activas")
    active = _fetch_sessions(organization_id, "active")

    for s in active:
        st.write(f"### Sesión {s['id']}")

        # Mostrar módulo asignado
        module = get_session_module(s)
        st.write(f"**Módulo:** {module['module_code']} — {module['name']}")

        # Mostrar producto
        product = get_product(s["product_id"])
        if product:
            st.write(f"Producto: **{product['name']}** — {product['price']}€")

        st.write(f"Aforo: {s['capacity']}")
        st.write(f"Pax registrados: {s['pax_registered']}")

    st.markdown("---")
    st.markdown("## 🟣 Sesiones Finalizadas / Expiradas")

    finished = _fetch_sessions(organization_id, "finished")
    expired = _fetch_sessions(organization_id, "expired")

    for s in finished + expired:
        st.write(f"### Sesión {s['id']}")

        module = get_session_module(s)
        st.write(f"**Módulo:** {module['module_code']} — {module['name']}")

        product = get_product(s["product_id"])
        if product:
            st.write(f"Producto: **{product['name']}** — {product['price']}€")

        st.write(f"Estado: {s['status']}")
        st.write(f"Finalizada en: {s.get('finished_at')}")
