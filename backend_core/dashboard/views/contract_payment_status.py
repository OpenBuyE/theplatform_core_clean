# backend_core/dashboard/views/contract_payment_status.py
import streamlit as st
import requests
from datetime import datetime

API_BASE = "http://localhost:8000"   # AJUSTA si usas Streamlit Cloud o similar


def render_contract_payment_status():
    st.title("📄 Contract & Payment Status")
    st.write("Vista completa del estado contractual y del flujo de pagos para una sesión determinada.")

    session_id = st.text_input("Session ID", placeholder="uuid-session")

    if not session_id:
        st.info("Introduce un Session ID para ver el estado contractual.")
        return

    if st.button("🔍 Consultar Contrato"):
        with st.spinner("Consultando estado contractual..."):
            try:
                url = f"{API_BASE}/internal/contract/{session_id}"
                resp = requests.get(url, timeout=10)
                if resp.status_code != 200:
                    st.error(f"Error {resp.status_code}: {resp.text}")
                    return
                data = resp.json()["data"]
            except Exception as e:
                st.error(f"Error al conectar con la API: {e}")
                return

        contract = data["contract"]
        payment = data["payment_session"]
        session_raw = data["session"]

        st.subheader("📌 Información de la Sesión")
        st.json(session_raw)

        st.subheader("📑 Estado Contractual")
        if contract:
            st.json(contract)
        else:
            st.warning("No existe ContractSession para esta sesión.")

        st.subheader("💳 Estado de Pagos")
        if payment:
            st.json(payment)
        else:
            st.warning("No existe PaymentSession para esta sesión.")

        # ---------------------------------------------------
        # Opcional: Acciones internas (admin/test/devtools)
        # ---------------------------------------------------

        st.divider()
        st.subheader("⚙️ Acciones Internas (Admin / Test)")

        # Request Settlement
        if st.button("Solicitar Settlement"):
            try:
                r = requests.post(
                    f"{API_BASE}/internal/contract/{session_id}/request-settlement",
                    json={"operator_user_id": "streamlit_admin"},
                    timeout=10,
                )
                st.success(r.json())
            except Exception as e:
                st.error(f"Error: {e}")

        # Confirm Delivery
        if st.button("Confirmar Entrega"):
            try:
                r = requests.post(
                    f"{API_BASE}/internal/contract/{session_id}/confirm-delivery",
                    json={
                        "adjudicatario_user_id": "streamlit_admin",
                        "delivery_method": "store_pickup",
                        "delivery_location": "Madrid - Centro",
                        "delivery_metadata": {"note": "Confirmado desde panel."}
                    },
                    timeout=10,
                )
                st.success(r.json())
            except Exception as e:
                st.error(f"Error: {e}")

        # Close Contract
        if st.button("Cerrar Contrato"):
            try:
                r = requests.post(
                    f"{API_BASE}/internal/contract/{session_id}/close-contract",
                    json={"operator_user_id": "streamlit_admin"},
                    timeout=10,
                )
                st.success(r.json())
            except Exception as e:
                st.error(f"Error: {e}")

