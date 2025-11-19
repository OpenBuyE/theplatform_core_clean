import streamlit as st
from backend_core.services.organization_repository import list_organizations

def render_sidebar():
    st.subheader("⚙️ Configuración")

    # --- Selector de organización ---
    orgs = list_organizations()

    if orgs:
        org_names = {org["name"]: org["id"] for org in orgs}

        selected = st.selectbox(
            "Organización activa",
            list(org_names.keys()),
            key="selected_organization_name"
        )

        st.session_state["organization_id"] = org_names[selected]
    else:
        st.warning("No hay organizaciones registradas.")

