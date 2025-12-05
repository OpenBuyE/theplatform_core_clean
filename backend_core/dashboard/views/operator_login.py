import streamlit as st
import bcrypt
from backend_core.services.supabase_client import table

# =========================================================
#  AUTH — DEBUG PRINT
# =========================================================
def debug(msg, data=None):
    st.markdown(f"🔍 **DEBUG:** {msg}")
    if data is not None:
        st.code(str(data))


# =========================================================
#  AUTHENTICATE OPERATOR
# =========================================================
def authenticate_operator(identifier: str, password: str):
    debug("Inicio authenticate_operator()")

    # 1. Leer operador por EMAIL exacto
    try:
        resp = (
            table("ca_operators")
            .select("*")
            .eq("email", identifier)
            .eq("active", True)
            .execute()
        )
    except Exception as e:
        st.error(f"❌ Error conectando con base de datos: {e}")
        return None

    data = resp.data
    debug("Respuesta Supabase:", data)

    if not data:
        debug("No se encontró ningún operador con ese email.")
        return None

    operator = data[0]
    debug("Operador obtenido:", operator)

    stored_hash = operator.get("password_hash")
    debug("Hash almacenado:", stored_hash)

    if not stored_hash:
        debug("El operador no tiene password_hash.")
        return None

    # 2. Validación bcrypt
    try:
        given_hash_result = bcrypt.checkpw(password.encode(), stored_hash.encode())
        debug("Resultado bcrypt.checkpw:", given_hash_result)
    except Exception as e:
        st.error(f"❌ Error verificando bcrypt: {e}")
        return None

    if given_hash_result:
        debug("Contraseña correcta ✔")
        return operator

    debug("Contraseña incorrecta ❌")
    return None


# =========================================================
#  RENDER LOGIN
# =========================================================
def render_operator_login():
    st.title("🔐 Operator Login — DEBUG MODE ACTIVADO")

    identifier = st.text_input("Email EXACTO (desde la tabla ca_operators)")
    password = st.text_input("Contraseña", type="password")

    if st.button("Iniciar Sesión"):
        operator = authenticate_operator(identifier, password)

        if operator:
            st.session_state["operator_id"] = operator["id"]
            st.session_state["email"] = operator.get("email")
            st.session_state["full_name"] = operator.get("full_name", "")
            st.session_state["role"] = operator.get("role", "")
            st.session_state["allowed_countries"] = operator.get("allowed_countries", [])
            st.session_state["global_access"] = operator.get("global_access", False)
            st.session_state["organization_id"] = operator.get("organization_id")

            st.success("🎉 Login correcto — Rerendering panel…")
            st.experimental_rerun()
        else:
            st.error("❌ Credenciales incorrectas o usuario no activo.")
