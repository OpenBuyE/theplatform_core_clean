# backend_core/dashboard/views/admin_operators_kyc.py

import streamlit as st
import requests

from backend_core.services.operator_repository import (
    list_operators,
    create_operator,
    list_operator_kyc_logs,
)

API_BASE = "http://localhost:8000"  # Ajusta si el backend corre en otro host/puerto


def render_admin_operators_kyc():
    st.title("Admin Operators / KYC")
    st.write("Gestión de operadores (organizaciones) y su estado KYC/KYB con MangoPay.")

    st.subheader("Crear nuevo operador")

    with st.form("create_operator_form"):
        org_id = st.text_input("Organization ID", placeholder="uuid de la organización")
        name = st.text_input("Nombre del operador (comercial o razón social)")
        country = st.text_input("País (ej: ES)", value="ES")
        legal_person_type = st.text_input("Legal Person Type (ej: BUSINESS)", value="BUSINESS")

        submitted = st.form_submit_button("Crear operador")

        if submitted:
            if not org_id or not name:
                st.error("Organization ID y Nombre son obligatorios.")
            else:
                op = create_operator(
                    organization_id=org_id,
                    name=name,
                    country=country or None,
                    legal_person_type=legal_person_type or None,
                )
                st.success(f"Operador creado: {op.id}")

    st.divider()

    st.subheader("Operadores registrados")

    operators = list_operators()
    if not operators:
        st.info("No hay operadores registrados todavía.")
        return

    for op in operators:
        st.markdown(f"### 🧩 Operador: **{op.name}**")
        st.write(f"- ID: `{op.id}`")
        st.write(f"- Organization ID: `{op.organization_id}`")
        st.write(f"- País: {op.country or '-'}")
        st.write(f"- Legal Person Type: {op.legal_person_type or '-'}")

        st.write(f"- KYC Status: **{op.kyc_status.value}**")
        st.write(f"- KYC Level: {op.kyc_level or '-'}")
        st.write(f"- MangoPay Legal User ID: `{op.mangopay_legal_user_id or '-'}`")
        st.write(f"- MangoPay Wallet ID: `{op.mangopay_wallet_id or '-'}`")

        # --------------------------------------------------
        # Botones de acciones MangoPay
        # --------------------------------------------------
        cols = st.columns(3)

        # 1) Crear cuenta MangoPay (Legal User + Wallet)
        with cols[0]:
            if st.button("Crear cuenta MangoPay", key=f"create_mgp_{op.id}"):
                try:
                    resp = requests.post(
                        f"{API_BASE}/internal/operators/{op.id}/create-mangopay-account",
                        timeout=20,
                    )
                    if resp.status_code == 200:
                        st.success("Cuenta MangoPay creada correctamente.")
                        st.json(resp.json())
                    else:
                        st.error(f"Error {resp.status_code}: {resp.text}")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

        # 2) Subir documento KYC (fake / test)
        with cols[1]:
            if st.button("Subir doc KYC (test)", key=f"upload_kyc_{op.id}"):
                try:
                    resp = requests.post(
                        f"{API_BASE}/internal/operators/{op.id}/upload-kyc-document",
                        timeout=20,
                    )
                    if resp.status_code == 200:
                        st.success("Documento KYC creado/enviado (modo test).")
                        st.json(resp.json())
                    else:
                        st.error(f"Error {resp.status_code}: {resp.text}")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

        # 3) Sincronizar estado KYC desde MangoPay
        with cols[2]:
            if st.button("Sync KYC Status", key=f"sync_kyc_{op.id}"):
                try:
                    resp = requests.get(
                        f"{API_BASE}/internal/operators/{op.id}/sync-kyc-status",
                        timeout=20,
                    )
                    if resp.status_code == 200:
                        st.success("Estado KYC sincronizado.")
                        st.json(resp.json())
                    else:
                        st.error(f"Error {resp.status_code}: {resp.text}")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

        # --------------------------------------------------
        # Logs KYC
        # --------------------------------------------------
        with st.expander("Ver logs KYC de este operador"):
            logs = list_operator_kyc_logs(op.id)
            if logs:
                st.json([l.dict() for l in logs])
            else:
                st.info("No hay logs KYC para este operador.")

        st.markdown("---")
