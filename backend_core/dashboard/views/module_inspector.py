# backend_core/dashboard/views/module_inspector.py

import streamlit as st

from backend_core.services.module_repository import (
    list_all_modules,
    assign_module_to_session,
)
from backend_core.services.session_repository import get_session_by_id


def render_module_inspector():
    st.title("🔍 Module Inspector")

    st.markdown(
        """
        Esta herramienta permite inspeccionar y reasignar módulos a sesiones.
        Útil para depuración interna y pruebas de comportamiento.
        """
    )

    # ========================================================
    # LISTAR MÓDULOS
    # ========================================================
    st.subheader("Módulos disponibles")

    modules = list_all_modules()

    if not modules:
        st.error("No hay módulos registrados.")
        return

    for m in modules:
        with st.expander(f"{m['module_code']} — {m['name']}"):
            st.write(m)

    st.markdown("---")

    # ========================================================
    # REASIGNAR MÓDULO A UNA SESIÓN
    # ========================================================
    st.subheader("Asignar módulo a sesión")

    session_id = st.text_input("Session ID")

    module_codes = {m["module_code"]: m["id"] for m in modules}

    selected_code = st.selectbox("Nuevo módulo", list(module_codes.keys()))
    selected_id = module_codes[selected_code]

    if st.button("Asignar módulo"):
        assign_module_to_session(session_id, selected_id)
        st.success(f"Módulo {selected_code} asignado a la sesión {session_id}")
        st.write("Detalles sesión:", get_session_by_id(session_id))
