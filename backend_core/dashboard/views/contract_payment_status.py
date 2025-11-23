# backend_core/dashboard/views/contract_payment_status.py

import streamlit as st
import requests

from backend_core.services.product_repository import get_product

API_BASE = "http://localhost:8000"   # AJUSTA si usas otro host/puerto


def render_contract_payment_status():
    st.title("📄 Contract & Payment Status")
    st.write("Vista completa del estado contractual y del flujo de pagos para una sesión.")

    session_id = st.text_input("Session ID", placeholder="uuid-session")

    if not session_id:
        st.info("Introduce un Session ID para ver el estado contractual.")
        return

    # ----------------------------------------------------
    # CONSULTAR CONTRATO
    # ----------------------------------------------------
    if st.button("🔍 Consultar Estado Contractual"):
        with st.spinner("Consultando contrato + pagos..."):
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

        # ----------------------------------------------------
        # PRODUCTO asociado
        # ----------------------------------------------------
        st.subheader("🛒 Producto asociado")
        product = get_product(session_raw["product_id"])

        if product:
            st.write(f"**{product['name']}** — {product['price_final']} €")
            if product.get("sku"):
                st.write(f"SKU: {product['sku']}")
            if product.get("description"):
                st.write(product["description"])
            if product.get("image_url"):
                st.image(product["image_url"], width=240)
        else:
            st.warning("Producto no encontrado en products_v2.")

        # ----------------------------------------------------
        # SESIÓN BRUTA
        # ----------------------------------------------------
        st.subheader("📌 Información de la Sesión")
        st.json(session_raw)

        # ----------------------------------------------------
        # CONTRACT SESSION
        # ----------------------------------------------------
        st.subheader("📑 Estado Contractual")
        if contract:
            st.json(contract)
        else:
            st.warning("No existe ContractSession para esta sesión.")

        # ----------------------------------------------------
        # PAYMENT SESSION
        # ----------------------------------------------------
        st.subheader("💳 Estado de Pagos")
        if payment:
            st.json(payment)
        else:
            st.warning("No existe PaymentSession para esta sesión.")

        # ----------------------------------------------------
        # ACCIONES INTERNAS
        # ----------------------------------------------------
        st.divider()
        st.subheader("⚙️ Acciones Internas (Admin/Test)")

        # Request Settlement
        if st.button("Solicitar Settlement"):
            try:
                r = requests.post(
                    f"{API_BASE}/internal/contract/{session_id}/request-settlement",
                    json={"operator_user_id": "streamlit_admin"},
                )
                st.success(r.json())
            except Exception as e:
                st.error(e)

        # Confirm Delivery
        if st.button("Confirmar Entrega"):
            try:
                r = requests.post(
                    f"{API_BASE}/internal/contract/{session_id}/confirm-delivery",
                    json={
                        "adjudicatario_user_id": "streamlit_admin",
                        "delivery_method": "store_pickup",
                        "delivery_location": "Madrid Centro",
                        "delivery_metadata": {"note": "Confirmado desde panel"},
                    },
                )
                st.success(r.json())
            except Exception as e:
                st.error(e)

        # Close Contract
        if st.button("Cerrar Contrato"):
            try:
                r = requests.post(
                    f"{API_BASE}/internal/contract/{session_id}/close-contract",
                    json={"operator_user_id": "streamlit_admin"},
                )
                st.success(r.json())
            except Exception as e:
                st.error(e)
