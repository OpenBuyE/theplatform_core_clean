# backend_core/dashboard/views/provider_manager_pro.py
# =======================================================
# PROVIDER MANAGER PRO — CRUD Completo
# =======================================================

import streamlit as st
from datetime import datetime

from backend_core.services.provider_repository_v2 import (
    list_providers,
    create_provider,
    update_provider,
    delete_provider,
)


def render_provider_manager_pro():
    st.title("🏭 Provider Manager Pro")
    st.write("Gestión profesional de proveedores (providers_v2).")

    st.markdown("---")

    providers = list_providers()
    provider_names = [p["name"] for p in providers] if providers else []

    # =======================================================
    # COLUMNA IZQUIERDA — LISTADO Y EDICIÓN
    # =======================================================
    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.subheader("📋 Proveedores existentes")

        if not providers:
            st.info("No hay proveedores registrados.")
        else:
            selected = st.selectbox(
                "Seleccionar proveedor para editar",
                provider_names,
            )

            provider = next(p for p in providers if p["name"] == selected)

            st.markdown("### ✏ Editar proveedor")
            with st.form("edit_provider_form"):
                name = st.text_input("Nombre", provider["name"])
                description = st.text_area("Descripción", provider.get("description", ""))
                contact_email = st.text_input("Email", provider.get("contact_email", ""))
                contact_phone = st.text_input("Teléfono", provider.get("contact_phone", ""))
                website = st.text_input("Web", provider.get("website", ""))
                active = st.checkbox("Activo", provider.get("active", True))

                submitted = st.form_submit_button("Actualizar")

            if submitted:
                update_provider(provider["id"], {
                    "name": name,
                    "description": description,
                    "contact_email": contact_email,
                    "contact_phone": contact_phone,
                    "website": website,
                    "active": active,
                })
                st.success("Proveedor actualizado correctamente.")
                st.experimental_rerun()

            # DELETE BUTTON
            st.markdown("---")
            if st.button("🗑 Eliminar proveedor", type="secondary"):
                delete_provider(provider["id"])
                st.warning("Proveedor eliminado.")
                st.experimental_rerun()

    # =======================================================
    # COLUMNA DERECHA — CREACIÓN
    # =======================================================
    with col2:
        st.subheader("➕ Crear nuevo proveedor")

        with st.form("create_provider_form"):
            new_name = st.text_input("Nombre *")
            new_description = st.text_area("Descripción")
            new_email = st.text_input("Email")
            new_phone = st.text_input("Teléfono")
            new_website = st.text_input("Web")

            submitted_new = st.form_submit_button("Crear proveedor", type="primary")

        if submitted_new:
            if not new_name:
                st.error("El nombre es obligatorio.")
            else:
                create_provider({
                    "name": new_name,
                    "description": new_description,
                    "contact_email": new_email,
                    "contact_phone": new_phone,
                    "website": new_website,
                    "active": True,
                    "organization_id": "11111111-1111-1111-1111-111111111111",
                    "created_at": datetime.utcnow().isoformat()
                })

                st.success("Proveedor creado correctamente.")
                st.experimental_rerun()
