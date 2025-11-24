# backend_core/dashboard/views/operator_dashboard.py

import streamlit as st

from backend_core.services.supabase_client import table
from backend_core.services.product_repository import get_product
from backend_core.services.module_repository import get_module_for_session
from backend_core.services.participant_repository import get_participants_for_session
from backend_core.services.session_repository import get_session_by_id


# =======================================================
# FETCH SESSIONS FOR OPERATOR
# =======================================================

def _fetch_sessions(organization_id: str, status: str):
    """
    Lee sesiones filtradas por operador y estado.
    """

    resp = (
        table("ca_sessions")
        .select("*")
        .eq("organization_id", organization_id)
        .eq("status", status)
        .order("activated_at" if status == "active" else "created_at")
        .execute()
    )

    return resp.data or []


# =======================================================
# MAIN VIEW
# =======================================================

def render_operator_dashboard():
    st.header("Operator Dashboard")

    org_id = st.text_input("Organization ID")

    if not org_id:
        st.info("Introduce organization_id para cargar el panel del operador.")
        return

    st.subheader("Sesiones activas")
    _render_sessions(org_id, "active")

    st.subheader("Sesiones parked")
    _render_sessions(org_id, "parked")

    st.subheader("Sesiones finalizadas")
    _render_sessions(org_id, "finished")


# =======================================================
# RENDER SESSION BLOCKS
# =======================================================

def _render_sessions(organization_id: str, status: str):
    sessions = _fetch_sessions(organization_id, status)

    if not sessions:
        st.info(f"No hay sesiones con estado '{status}'.")
        return

    for s in sessions:
        st.write("----")
        st.write(f"### Sesión: {s['id']} — Estado: {s['status']}")

        # Producto
        product = get_product(s["product_id"])
        if product:
            st.write(f"- Producto: **{product['name']}** — {product['price']}€")

        # Módulo
        module = get_module_for_session(s["id"])
        if module:
            st.write(f"- Módulo: **{module['module_code']}** ({module['id']})")
            st.write(f"  Estado módulo: {module['module_status']}")
            st.write(f"  ¿Tiene adjudicatario?: {module['has_award']}")

        # Participantes
        participants = get_participants_for_session(s["id"])
        if participants:
            st.write("#### Participantes")
            for p in participants:
                awarded = " ✅" if p.get("is_awarded") else ""
                st.write(f"- {p['id']} — user {p['user_id']}{awarded}")
        else:
            st.write("No hay participantes.")

        st.write("----")
