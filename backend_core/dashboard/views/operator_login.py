import streamlit as st
import bcrypt
from backend_core.services.supabase_client import table

# ---------------------------------------------------------
# Operator Login — MODO DIAGNÓSTICO
# ---------------------------------------------------------

def authenticate_operator(identifier: str, password: str):
    """
    (MODO DIAGNOSTICO)
    Esta función NO se usa mientras debug está activo.
    Se deja aquí por coherencia, pero no interviene.
    """
    try:
        resp = (
            table("ca_operators")
            .select("*")
            .eq("email", identifier)
            .eq("active", True)
            .execute()
        )
    except Exception as e:
        st.error(f"Error conectando con la base de datos: {e}")
        return None

    data = resp.data

    if not data:
        return None

    operator = data[0]
    stored_hash = operator.get("password_hash")

    try:
        if bcrypt.checkpw(password.encode(), stored_hash.encode()):
            return operator
    except:
        return None

    return None


def render_operator_login():
    st.warning("🟡 LOGIN EN MODO DIAGNÓSTICO — NO SE VALIDAN CREDENCIALES")
    st.title("🔐 Operator Login (Debug Mode)")

    st.markdown("### Acceso al Panel Administrativo (modo diagnóstico)")
    st.markdown("**El login REAL está desactivado temporalmente.**")

    identifier = st.text_input("Usuario / Email (ignorado en debug)")
    password = st.text_input("Contraseña (ignorado en debug)", type="password")

    if st.button("Iniciar Sesión"):
        # --------------------------------------------------------
        # 🔥 MODO DIAGNÓSTICO: ENTRADA DIRECTA SIN COMPROBAR LOGIN
        # --------------------------------------------------------
        st.session_state["operator_id"] = "debug-operator"
        st.session_state["email"] = "debug@example.com"
        st.session_state["username"] = "debug"
        st.session_state["full_name"] = "Debug Access"
        st.session_state["role"] = "admin_master"
        st.session_state["allowed_countries"] = ["ES", "PT", "FR", "IT", "DE"]
        st.session_state["global_access"] = True
        st.session_state["organization_id"] = "debug-org"

        st.success("Accediendo al panel SIN LOGIN (modo diagnóstico)…")
        st.experimental_rerun()

    st.markdown("---")
    st.info("Modo diagnóstico activo. El login real volverá después de depurar el fallo.")
