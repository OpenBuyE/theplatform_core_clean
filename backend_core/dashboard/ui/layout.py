import streamlit as st
from backend_core.services.organization_repository import list_organizations


def render_app_header():
    """Header superior del panel."""
    st.markdown(
        """
        <h1 style="margin-bottom:0;">Compra Abierta – Panel Operativo</h1>
        <p style="color:gray;margin-top:0;">Backend Operativo · Multi-Tenant</p>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")


def render_sidebar():
    """Sidebar con selector de organización."""
    st.subheader("⚙️ Configuración")

    # Cargar organizaciones desde Supabase
    orgs = list_organizations()

    if not orgs:
        st.warning("⚠️ No hay organizaciones creadas.")
        st.session_state["organization_id"] = None
        return

    # Mapa: nombre → id
    org_names = {org["name"]: org["id"] for org in orgs}

    # Valor por defecto persistente
    default_name = st.session_state.get(
        "selected_organization_name",
        list(org_names.keys())[0]
    )

    # Selector
    selected = st.selectbox(
        "Organización activa",
        list(org_names.keys()),
        index=list(org_names.keys()).index(default_name)
        if default_name in org_names else 0,
        key="selected_organization_name"
    )

    # Guardar ID de organización seleccionada
    st.session_state["organization_id"] = org_names[selected]

    st.info(f"Organización activa: **{selected}**")
    st.markdown("---")

