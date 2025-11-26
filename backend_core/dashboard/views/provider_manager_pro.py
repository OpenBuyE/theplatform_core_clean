import streamlit as st
from backend_core.services.provider_repository import (
    list_providers,
    create_provider,
    update_provider,
    delete_provider
)

def render_provider_manager_pro():
    st.title("🏢 Provider Manager Pro")

    # ================================
    # LISTADO DE PROVEEDORES
    # ================================
    st.subheader("Listado de Proveedores")

    providers = list_providers()

    if not providers:
        st.info("No hay proveedores registrados aún.")
    else:
        st.dataframe(providers, width='stretch')

    st.markdown("---")

    # ================================
    # CREAR NUEVO PROVEEDOR
    # ================================
    st.subheader("➕ Crear nuevo proveedor")

    with st.form("create_provider_form"):
        name = st.text_input("Nombre")
        email = st.text_input("Email")
        phone = st.text_input("Teléfono")

        submitted = st.form_submit_button("Crear proveedor")

        if submitted:
            if not name:
                st.error("El nombre es obligatorio.")
            else:
                try:
                    create_provider(name=name, email=email, phone=phone)
                    st.success("Proveedor creado correctamente.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error creando proveedor: {e}")

    st.markdown("---")

    # ================================
    # EDITAR PROVEEDOR
    # ================================
    st.subheader("✏️ Editar proveedor existente")

    provider_ids = [p["id"] for p in providers] if providers else []

    if provider_ids:
        selected_id = st.selectbox("Seleccione proveedor", provider_ids)

        selected_provider = next((p for p in providers if p["id"] == selected_id), None)

        if selected_provider:
            with st.form("edit_provider_form"):
                edit_name = st.text_input("Nombre", selected_provider["name"])
                edit_email = st.text_input("Email", selected_provider["email"])
                edit_phone = st.text_input("Teléfono", selected_provider["phone"])

                submitted_edit = st.form_submit_button("Guardar cambios")

                if submitted_edit:
                    try:
                        update_provider(
                            provider_id=selected_id,
                            name=edit_name,
                            email=edit_email,
                            phone=edit_phone,
                        )
                        st.success("Proveedor actualizado correctamente.")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error editando proveedor: {e}")

    st.markdown("---")

    # ================================
    # ELIMINAR PROVEEDOR
    # ================================
    st.subheader("🗑 Eliminar proveedor")

    if provider_ids:
        selected_id_delete = st.selectbox("Seleccione proveedor a eliminar", provider_ids, key="delete_provider")

        if st.button("Eliminar proveedor"):
            try:
                delete_provider(provider_id=selected_id_delete)
                st.success("Proveedor eliminado correctamente.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error eliminando proveedor: {e}")
