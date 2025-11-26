import streamlit as st
import bcrypt
from backend_core.services.supabase_client import table

# ---------------------------------------------------------
# Operator Login — Email + Password + Control de Roles/Paises
# ---------------------------------------------------------

def authenticate_operator(email: str, password: str):
    """
    Autentica a un operador contra la tabla ca_operators.
    Devuelve datos completos del operador si la contraseña coincide.
    """
    try:
        result = (
            table("ca_operators")
            .select("*")
            .eq("email", email)
            .eq("active", True)
            .execute()
        )
    except Exception as e:
        st.error(f"Error conectando con la base de datos: {e}")
        return None

    if not result or len(result) == 0:
        return None

    operator = result[0]

    stored_hash = operator.get("password_hash", "")
    if not stored_hash:
        return None

    # Validar contraseña usando bcrypt
    if bcrypt.checkpw(password.encode(), stored_hash.encode()):
        return operator

    return None


def render_operator_login():
    st.title("🔐 Operator Login")

    st.markdown("### Acceso al Panel Administrativo")
    st.markdown("Use sus credenciales para acceder al sistema.")

    # Campos del formulario
    email = st.text_input("Usuario / Email")
    password = st.text_input("Contraseña", type="password")

    if st.button("Iniciar Sesión"):
        operator = authenticate_operator(email, password)

        if operator:
            # Éxito — cargar credenciales en la sesión
            st.session_state["operator_id"] = operator["id"]
            st.session_state["email"] = operator["email"]
            st.session_state["full_name"] = operator.get("full_name", "")
            st.session_state["role"] = operator.get("role", "operator")
            st.session_state["allowed_countries"] = operator.get("allowed_countries", [])
            st.session_state["global_access"] = operator.get("global_access", False)
            st.session_state["organization_id"] = operator.get("organization_id")

            st.success("Autenticación correcta. Accediendo al panel...")
            st.experimental_rerun()

        else:
            st.error("❌ Credenciales incorrectas o usuario no activo.")

    st.markdown("---")
    st.info("Si tiene problemas para acceder, contacte con un Admin Master.")
