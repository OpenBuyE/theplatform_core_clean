import streamlit as st
import bcrypt
from backend_core.services.supabase_client import table

# ---------------------------------------------------------
# Operator Login — Email + Password
# ---------------------------------------------------------

def authenticate_operator(identifier: str, password: str):
    """
    Autentica a un operador usando SOLO email.
    (La columna 'username' NO existe en la tabla actual.)
    """
    try:
        result = (
            table("ca_operators")
            .select("*")
            .eq("email", identifier)     # <-- CORRECCIÓN CRÍTICA
            .eq("active", True)
            .execute()
        )
    except Exception as e:
        st.error(f"Error conectando con la base de datos: {e}")
        return None

    if not result or len(result) == 0:
        return None

    operator = result[0]

    stored_hash = operator.get("password_hash")
    if not stored_hash:
        return None

    if bcrypt.checkpw(password.encode(), stored_hash.encode()):
        return operator

    return None


def render_operator_login():
    st.title("🔐 Operator Login")

    st.markdown("### Acceso al Panel Administrativo")
    st.markdown("Use su *email* para acceder.")

    identifier = st.text_input("Usuario / Email")
    password = st.text_input("Contraseña", type="password")

    if st.button("Iniciar Sesión"):
        operator = authenticate_operator(identifier, password)

        if operator:
            st.session_state["operator_id"] = operator["id"]
            st.session_state["email"] = operator.get("email")
            # La tabla no contiene username, pero mantenemos la clave para compatibilidad
            st.session_state["username"] = operator.get("username")
            st.session_state["full_name"] = operator.get("full_name", "")
            st.session_state["role"] = operator.get("role", "operator")
            st.session_state["allowed_countries"] = operator.get("allowed_countries", [])
            st.session_state["global_access"] = operator.get("global_access", False)
            st.session_state["organization_id"] = operator.get("organization_id")

            st.success("Autenticación correcta. Accediendo al panel…")
            st.experimental_rerun()
        else:
            st.error("❌ Credenciales incorrectas o usuario no activo.")

    st.markdown("---")
    st.info("Si tiene problemas para acceder, contacte con un Admin Master.")
