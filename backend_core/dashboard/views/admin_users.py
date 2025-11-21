import streamlit as st

def render_admin_users():
    st.title("👥 Admin Users (Deshabilitado temporalmente)")
    st.info(
        """
        El módulo de gestión de usuarios está temporalmente deshabilitado
        mientras completamos la migración a la nueva arquitectura del backend.
        
        ✔ El resto del panel funciona correctamente.  
        ✔ La lógica de sesiones, motor, adjudicación y seeds está operativa.

        Este módulo volverá cuando integremos el sistema de autenticación final.
        """
    )

