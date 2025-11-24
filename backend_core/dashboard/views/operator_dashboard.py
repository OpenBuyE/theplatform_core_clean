# backend_core/dashboard/views/operator_dashboard.py

import streamlit as st
import requests

from backend_core.services import supabase_client
from backend_core.services.product_repository import get_product

API_BASE = "http://localhost:8000"  # ajusta si tu backend expone otra URL


def _fetch_sessions(organization_id: str, status: str):
    resp = (
        supabase_client.table("ca_sessions")
        .select("*")
        .eq("organization_id", organization_id)
        .eq("status", status)
        .order("activated_at" if status == "active" else "created_at", desc=True)
        .execute()
    )
    return resp.data or []


def _fetch_participants(session_id: str):
    resp = (
        supabase_client.table("ca_session_participants")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []


def _render_session_card(session: dict):
    st.markdown(f"### 🧾 Sesión: `{session['id']}`")
    st.write(f"- Estado: **{session['status']}**")
    st.write(f"- Serie: `{session.get('series_id')}`")
    st.write(f"- Sequence number: {session.get('sequence_number')}")
    st.write(f"- Aforo: {session.get('capacity')} — Pax registrados: {session.get('pax_registered')}")
    st.write(f"- Activada: {session.get('activated_at')}")
    st.write(f"- Expira: {session.get('expires_at')}")
    st.write(f"- Finalizada: {session.get('finished_at')}")

    # Producto
    product = get_product(session["product_id"])
    st.markdown("#### 🛒 Producto")

    if product:
        st.write(f"**{product['name']}** — {product.get('price_final', 'N/A')} €")
        if product.get("sku"):
            st.write(f"SKU: `{product['sku']}`")
        if product.get("description"):
            st.write(product["description"])
        if product.get("image_url"):
            st.image(product["image_url"], width=220)
    else:
        st.warning("Producto no encontrado en products_v2.")

    # Participantes (solo lectura)
    with st.expander("👥 Ver participantes"):
        participants = _fetch_participants(session["id"])
        if participants:
            st.json(participants)
        else:
            st.info("No hay participantes registrados en esta sesión.")

    # Contrato & pagos (solo lectura, usando API interna)
    with st.expander("📄 Ver estado contractual y pagos"):
        try:
            resp = requests.get(f"{API_BASE}/internal/contract/{session['id']}", timeout=10)
            if resp.status_code == 200:
                data = resp.json()["data"]
                st.write("**Contrato:**")
                st.json(data.get("contract"))
                st.write("**Payment Session:**")
                st.json(data.get("payment_session"))
                st.write("**Sesión (raw):**")
                st.json(data.get("session"))
            else:
                st.error(f"Error {resp.status_code} al consultar el contrato.")
        except Exception as e:
            st.error(f"Error al conectar con la API interna: {e}")

    st.markdown("---")


def render_operator_dashboard():
    st.title("Vista Operador Real")
    st.write("Panel operativo de uso diario para un operador real (sin acciones de debug).")

    organization_id = st.text_input(
        "Organization ID del operador",
        placeholder="uuid de la organización",
        help="Filtra todas las sesiones, contratos y pagos a nivel de organización.",
    )

    if not organization_id:
        st.info("Introduce un Organization ID para ver el panel del operador.")
        return

    tabs = st.tabs(["Sesiones activas", "Sesiones parked", "Sesiones finalizadas"])

    # SESIONES ACTIVAS
    with tabs[0]:
        st.subheader("Sesiones activas")
        active_sessions = _fetch_sessions(organization_id, "active")
        if not active_sessions:
            st.info("No hay sesiones activas para esta organización.")
        else:
            for s in active_sessions:
                _render_session_card(s)

    # SESIONES PARKED
    with tabs[1]:
        st.subheader("Sesiones parked")
        resp = (
            supabase_client.table("ca_sessions")
            .select("*")
            .eq("organization_id", organization_id)
            .eq("status", "parked")
            .order("created_at", desc=True)
            .execute()
        )
        parked_sessions = resp.data or []
        if not parked_sessions:
            st.info("No hay sesiones parked para esta organización.")
        else:
            for s in parked_sessions:
                _render_session_card(s)

    # SESIONES FINALIZADAS
    with tabs[2]:
        st.subheader("Sesiones finalizadas (finished / expired)")
        resp = (
            supabase_client.table("ca_sessions")
            .select("*")
            .eq("organization_id", organization_id)
            .in_("status", ["finished", "expired"])
            .order("finished_at", desc=True)
            .limit(100)
            .execute()
        )
        finished_sessions = resp.data or []
        if not finished_sessions:
            st.info("No hay sesiones finalizadas para esta organización.")
        else:
            for s in finished_sessions:
                _render_session_card(s)
