# backend_core/dashboard/views/contract_payment_status.py

import streamlit as st

from backend_core.services.contract_engine import contract_engine
from backend_core.services.session_repository import get_session_by_id
from backend_core.services.participant_repository import get_participants_for_session
from backend_core.services.product_repository import get_product
from backend_core.services.module_repository import get_session_module


# =======================================================
# CONTRACT & PAYMENT STATUS – MÓDULO AWARE
# =======================================================

def render_contract_payment_status():

    st.header("📄 Contract & Payment Status")

    session_id = st.text_input("Session ID:", placeholder="UUID de la sesión")

    if not session_id:
        st.info("Introduce un Session ID.")
        return

    st.markdown("---")

    # =======================================================
    # Obtener estado contractual completo
    # =======================================================

    data = contract_engine.get_contract_status(session_id)

    if not data:
        st.error("Sesión no encontrada.")
        return

    session = data["session"]
    module = data["module"]
    payment = data["payment"]

    st.subheader(f"Sesión {session['id']}")
    st.write(f"**Estado:** {session['status']}")
    st.write(f"**Módulo:** {module['module_code']} — {module['name']}")

    # =======================================================
    # Mostrar información del producto
    # =======================================================

    product = get_product(session["product_id"])
    if product:
        st.write(f"📦 Producto: **{product['name']}** — {product['price']} €")
        if product.get("image_url"):
            st.image(product["image_url"], width=200)

    st.markdown("---")

    # =======================================================
    # MÓDULO C — PRELAUNCH
    # =======================================================

    if module["module_code"] == "C_PRELAUNCH":
        st.warning("🔒 Módulo PRELAUNCH — No existe flujo de contrato ni pagos.")
        st.info("Esta sesión es únicamente informativa y no admite participantes.")
        return

    # =======================================================
    # MÓDULO B — AUTO-EXPIRE
    # =======================================================

    if module["module_code"] == "B_AUTO_EXPIRE":
        st.info("🕒 Módulo AUTO-EXPIRE — No existe flujo de contrato ni pagos.")
        st.write("La sesión expirará automáticamente si no completa aforo.")
        return

    # =======================================================
    # MÓDULO A — DETERMINISTA (ÚNICO con flujo contractual)
    # =======================================================

    if module["module_code"] == "A_DETERMINISTIC":

        st.success("Módulo determinista — flujo contractual habilitado.")

        st.markdown("### 👤 Participantes")
        participants = get_participants_for_session(session_id)
        st.json(participants)

        st.markdown("### 📌 Estado contractual")
        if payment:
            st.write(f"**Payment Status:** {payment['status']}")
            st.write(f"Total depositado: {payment.get('total_deposited_amount', 0)} €")
            st.write(f"Adjudicatario: {payment.get('awarded_participant_id', '—')}")

            st.markdown("### 📬 Datos complementarios")
            st.json(payment)
        else:
            st.info("La sesión aún no ha iniciado flujo contractual.")

        st.markdown("---")
        st.subheader("ℹ Logs de contrato (desde auditoría)")
        st.write("Consulta completa en Audit Logs.")
