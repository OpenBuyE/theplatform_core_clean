# backend_core/dashboard/views/module_inspector.py

import streamlit as st

from backend_core.services.module_repository import (
    list_modules,
    assign_module_to_session,
)
from backend_core.services.supabase_client import table
from backend_core.services.module_repository import get_module
from backend_core.services.audit_repository import log_event


SESSIONS_TABLE = "ca_sessions"


# =======================================================
#   MODULE INSPECTOR – PANEL PROFESIONAL
# =======================================================

def render_module_inspector():

    st.header("🧩 Module Inspector")
    st.write("Vista avanzada para gestionar módulos del sistema.")

    st.markdown("---")

    # =======================================================
    # LISTAR MÓDULOS
    # =======================================================

    st.subheader("📚 Módulos registrados")

    modules = list_modules()

    for m in modules:
        with st.expander(f"{m['module_code']} — {m['name']}"):
            st.write(f"**Código:** {m['module_code']}")
            st.write(f"**Nombre:** {m['name']}")
            st.write(f"**Descripción:** {m.get('description', '—')}")
            st.write(f"**Activo:** {'Sí' if m.get('active') else 'No'}")
            st.write("---")

            # Ver sesiones asociadas a este módulo
            st.write("### Sesiones con este módulo")

            resp = (
                table(SESSIONS_TABLE)
                .select("*")
                .eq("module_code", m["module_code"])
                .order("created_at", desc=True)
                .execute()
            )
            sessions = resp.data or []

            if not sessions:
                st.info("No hay sesiones con este módulo.")
            else:
                for s in sessions[:10]:
                    st.write(f"- Sesión: {s['id']} — Estado: **{s['status']}**")

    st.markdown("---")

    # =======================================================
    # CAMBIO DE MÓDULO PARA SESIONES EXISTENTES
    # =======================================================

    st.subheader("🛠 Cambiar módulo de una sesión")

    session_id = st.text_input("Session ID a modificar:")

    if session_id:
        st.write("Seleccionar nuevo módulo:")

        module_labels = {f"{m['module_code']} — {m['name']}": m["module_code"] for m in modules}

        selected_label = st.selectbox(
            "Módulo:",
            options=list(module_labels.keys()),
        )

        new_code = module_labels[selected_label]

        if st.button("Aplicar cambio de módulo"):
            try:
                assign_module_to_session(session_id, new_code)

                log_event(
                    "module_changed_manual",
                    session_id=session_id,
                    user_id=None,
                    metadata={"new_module": new_code},
                )

                st.success(f"Módulo cambiado correctamente a: {new_code}")
            except Exception as e:
                st.error(f"Error cambiando módulo: {e}")

    st.markdown("---")

    # =======================================================
    # BUSCAR SESIONES POR MÓDULO
    # =======================================================

    st.subheader("🔍 Buscar sesiones por módulo")

    search_label = st.selectbox(
        "Selecciona módulo a buscar:",
        options=[m["module_code"] for m in modules],
    )

    if st.button("Buscar"):
        resp = (
            table(SESSIONS_TABLE)
            .select("*")
            .eq("module_code", search_label)
            .order("created_at", desc=True)
            .execute()
        )
        sessions = resp.data or []

        st.write(f"### Resultados ({len(sessions)})")

        for s in sessions[:25]:
            st.write(
                f"- **{s['id']}** — estado: {s['status']} — product_id: {s['product_id']}"
            )
