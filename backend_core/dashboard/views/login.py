import streamlit as st

def render():
    st.warning("🟡 LOGIN EN MODO DIAGNÓSTICO — ACCESO DIRECTO ACTIVADO")
    st.title("🔐 Operator Login (Debug Mode)")

    st.markdown("### Acceso al Panel Administrativo (modo diagnóstico)")
    st.markdown("El login real está temporalmente deshabilitado.")

    st.text_input("Usuario / Email (ignorado en debug)")
    st.text_input("Contraseña (ignorado en debug)", type="password")

    if st.button("Iniciar Sesión"):
        # 🔥 ACCESO DIRECTO SIN VALIDACIÓN
        st.session_state["operator_id"] = "debug-operator"
        st.session_state["email"] = "debug@example.com"
        st.session_state["role"] = "admin_master"
        st.session_state["full_name"] = "Debug Access"
        st.session_state["allowed_countries"] = ["ES", "PT", "FR", "IT", "DE"]
        st.session_state["global_access"] = True
        st.session_state["organization_id"] = "debug-org"

        st.success("Accediendo al panel SIN login…")
        st.experimental_rerun()

    st.markdown("---")
    st.info("Modo diagnóstico activo. El login real volverá después de depurar.")
