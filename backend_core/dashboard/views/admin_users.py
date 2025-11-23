# backend_core/dashboard/views/admin_users.py

import streamlit as st

from backend_core.services import supabase_client


def render_admin_users():
    st.title("Admin Users")
    st.write("Gestión básica de usuarios (vista solo lectura por ahora).")

    # Aquí asumimos una tabla genérica de usuarios, ajusta el nombre si es distinto.
    # Si aún no existe, esta vista solo mostrará información de ejemplo.
    try:
        resp = (
            supabase_client.table("ca_users")
            .select("*")
            .limit(100)
            .execute()
        )
        users = resp.data or []
        if users:
            st.json(users)
        else:
            st.info("No hay usuarios o la tabla ca_users está vacía.")
    except Exception:
        st.warning(
            "La tabla 'ca_users' no existe todavía. "
            "Esta vista está preparada para el futuro módulo de usuarios."
        )
