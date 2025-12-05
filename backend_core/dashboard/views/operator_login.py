import streamlit as st
import bcrypt
from backend_core.services.supabase_client import table

# ---------------------------------------------------------
# Operator Login — Email + Password
# ---------------------------------------------------------

def authenticate_operator(identifier: str, password: str):
    """
    Autentica a un operador usando SOLO email.
    Compatible con Supabase v2 (APIResponse con .data).
    """

    # MODO DEBUG ESPECIAL — si el usuario escribe "debug"
    if identifier == "debug":
        st.warning("🟡 MODO DEBUG ACTIVADO — Mostrando información interna del operador GlobalAdmin")

        resp = (
            table("ca_operators")
            .select("*")
            .eq("email", "GlobalAdmin")
            .execute()
        )

        data = resp.data

        if not data:
            st.error("❌ No se encontró GlobalAdmin en la tabla.")
            return None

        operator = data[0]
        stored_hash = operator.get("password_hash")

        st.write("🔍 HASH EN BASE DE DATOS:", stored_hash)
        st.write("🔍 LONGITUD HASH:", len(stored_hash) if stored_hash else "None")

        try:
            ok = bcrypt.checkpw(password.encode(), stored_hash.encode())
            st.write("🔍 RESULTADO bcrypt.checkpw():", ok)
        except Exception as e:
            st.error(f"ERROR verificando bcrypt: {e}")

        return None  # No hacemos login real en modo debug

    # MODO NORMAL
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

    data = resp.data  # <-- CORRECCIÓN IMPORTANTE

    if not data or len(data) == 0:
        return None

    operator = data[0]

    stored_hash = operator.get("password_hash")
    if not stored_hash:
        return None

    # Validación bcrypt
    try:
        if bcrypt.checkpw(password.encode(), stored_hash.encode()):
            return operator
    except Exception as e:
        st.error(f"Error verificando la contraseña: {e}")
        return None

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
            st.session_state["username"] = operator.get("username")  # no existe, queda None
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
