import streamlit as st
from backend_core.services.session_manager import login, logout, is_logged_in


def render_login():
    """
    Pantalla de login.
    Si el usuario ya está autenticado, muestra opción de logout.
    """

    st.title("🔐 Acceso al Panel Operativo")

    if is_logged_in():
        st.success(f"Sesión iniciada como: **{st.session_state['user_email']}**")
        if st.button("Cerrar sesión"):
            logout()
            st.experimental_rerun()
        return

    st.markdown("Introduce tus credenciales para acceder:")

    with st.form("login_form"):
        email = st.text_input("Email", "")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Iniciar sesión")

        if submitted:
            if login(email, password):
                st.success("Acceso correcto. Redirigiendo...")
                st.experimental_rerun()
            else:
                st.error("Credenciales incorrectas. Inténtalo de nuevo.")

    st.markdown("---")
    st.info("Si no tienes cuenta, solicita acceso al administrador del sistema.")
