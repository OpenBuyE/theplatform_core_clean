# backend_core/dashboard/views/contract_payment_status.py

import streamlit as st

from backend_core.services.session_repository import get_session_by_id
from backend_core.services.participant_repository import get_participants_for_session
from backend_core.services.product_repository import get_product
from backend_core.services.module_repository import get_module_for_session
from backend_core.services.payment_state_machine import get_payment_session


# =======================================================
# VISTA: CONTRACT & PAYMENT STATUS
# =======================================================

def render_contract_payment_status():
    st.header("Contract & Payment Status")

    session_id = st.text_input("Introduce el ID de la sesión")

    if not session_id:
        st.info("Introduce un session_id para ver el estado contractual y de pagos.")
        return

    if st.button("Consultar estado"):
        _render_session_status(session_id)


def _render_session_status(session_id: str):
    # -------------------------
    # Sesión
    # -------------------------
    session = get_session_by_id(session_id)
    if not session:
        st.error(f"No se ha encontrado la sesión {session_id}.")
        return

    st.subheader("Datos de la sesión")
    st.write(f"**Session ID:** {session['id']}")
    st.write(f"**Estado:** {session['status']}")
    st.write(f"**Aforo:** {session['pax_registered']} / {session['capacity']}")
    st.write(f"**Series ID:** {session.get('series_id')}")
    st.write(f"**Sequence #:** {session.get('sequence_number')}")
    st.write(f"**Activated at:** {session.get('activated_at')}")
    st.write(f"**Finished at:** {session.get('finished_at')}")

    # -------------------------
    # Producto
    # -------------------------
    product = get_product(session["product_id"])
    if product:
        st.subheader("Producto")
        st.write(f"**Nombre:** {product['name']}")
        st.write(f"**Precio:** {product['price']}€")

    # -------------------------
    # Módulo
    # -------------------------
    module = get_module_for_session(session_id)
    if module:
        st.subheader("Módulo")
        st.write(f"**Module ID:** {module['id']}")
        st.write(f"**Module Code:** {module['module_code']}")
        st.write(f"**Module Status:** {module.get('module_status')}")
        st.write(f"**Has Award:** {module.get('has_award')}")

    # -------------------------
    # Participantes
    # -------------------------
    participants = get_participants_for_session(session_id)
    st.subheader("Participantes")

    if not participants:
        st.info("La sesión no tiene participantes.")
    else:
        for p in participants:
            awarded = " ✅ ADJUDICATARIO" if p.get("is_awarded") else ""
            st.write(
                f"- Participant ID: {p['id']} — User: {p['user_id']} — "
                f"Amount: {p['amount']} — Qty: {p['quantity']}{awarded}"
            )

    # -------------------------
    # Estado de pagos (Payment State Machine)
    # -------------------------
    st.subheader("Payment State")

    payment = get_payment_session(session_id)
    if not payment:
        st.info("No existe todavía un registro en la Payment State Machine para esta sesión.")
        return

    st.write(f"**Payment State:** {payment.get('state')}")
    st.write(f"**Created at:** {payment.get('created_at')}")
    st.write(f"**Updated at:** {payment.get('updated_at')}")
    st.write(f"**Metadata:** {payment}")
