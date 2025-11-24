# backend_core/dashboard/views/module_inspector.py

import streamlit as st

from backend_core.services.module_repository import (
    list_all_modules,
    assign_module,
)
from backend_core.services.session_repository import get_session_by_id
from backend_core.services.product_repository import get_product


# =======================================================
# MODULE INSPECTOR VIEW
# =======================================================

def render_module_inspector():
    st.header("Module Inspector")

    st.write(
        "Esta herramienta permite ver los módulos disponibles "
        "y asignar manualmente un módulo a una sesión."
    )

    st.subheader("Listado de módulos registrados")
    modules = list_all_modules()

    if not modules:
        st.warning("No hay módulos registrados.")
    else:
        for m in modules:
            st.write("----")
            st.write(f"**ID:** {m['id']}")
            st.write(f"**Código:** {m['module_code']}")
            st.write(f"**Nombre:** {m['name']}")
            st.write(f"**Descripción:** {m['description']}")
            st.write(f"**Activo:** {m['is_active']}")

    st.write("----")
    st.subheader("Asignar módulo a una sesión")

    session_id = st.text_input("Session ID")

    module_codes = {m["module_code"]: m["id"] for m in modules}
    if module_codes:
        selected_module_code = st.selectbox("Módulo", list(module_codes.keys()))
        selected_module_id = module_codes[selected_module_code]

        if st.button("Asignar módulo"):
            assign_module(session_id, selected_module_id)
            st.success(
                f"Módulo '{selected_module_code}' asignado a la sesión {session_id}."
            )
    else:
        st.info("No hay módulos activos para asignar.")
