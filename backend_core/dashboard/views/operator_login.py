import streamlit as st
import bcrypt
from backend_core.services.supabase_client import table

# ====================================================
#  Helper para normalizar respuestas de Supabase
# ====================================================

def _extract_data(result):
    """
    Normaliza la respuesta de Supabase.
    Devuelve siempre una LISTA de diccionarios.
    """
    if result is None:
        return []

    # Caso 1: supabase-py devuelve {"data": [...], ...}
    if isinstance(result, dict) and "data" in result:
        return result.get("data") or []

    # Caso 2: SDK devuelve resultados directamente como lista
    if isinstance(result, list):
        return result

    # Caso 3: objeto con atributo .data (algunos SDK)
    if hasattr(result, "data"):
        return result.data or []

    # Caso extremo: desconocido → devolver vacío
    return []


# ====================================================
#  Lógica de autenticación
# ====================================================

def authenticate_operator(email: str, password: str):
    """
    Autentica al operador según ca_operators.
    """
    try:
        raw = (
            table("ca_operators")
            .select("*")
            .eq("email", email)
            .eq("active", True)
            .execute()
        )
    except Exception as e:
        st.error(f"Error conectando con la base de datos: {e}")
        return None

    operators = _extract_data(raw)

    if not operators:
        return None

    operator = operators[0]

    stored_hash = operator.get("password_hash")
    if not stored_hash:
        return None

    try:
        valid = bcrypt.checkpw(password.encode(), stored_hash.encode())
    except Exception:
        return None

    return operator if valid else None


# ====================================================
#  UI — Login
# ====================================================

def render_operator_login():
    st.title("🔐 Operator Login")

    st.markdown("### Acceso al Panel Administrativo")

    email = st.text_input("Usuario / Email")
    password = st.text_input("Contraseña", type="password")

    if st.button("Iniciar Sesión"):
        operator = authenticate_operator(email, password)

        if operator:
            # Guardar en sesión
            st.session_state["operator_id"] = operator["id"]
            st.session_state["email"] = operator["email"]
            st.session_state["full_name"] = operator.get("full_name", "")
            st.session_state["role"] = operator.get("role", "operator")
            st.session_state["allowed_countries"] = operator.get("allowed_countries", [])
            st.session_state["global_access"] = operator.get("global_access", False)
            st.session_state["organization_id"] = operator.get("organization_id")

            st.success("Autenticación correcta. Accediendo…")
            st.experimental_rerun()

        else:
            st.error("❌ Credenciales incorrectas o usuario no activo.")

    st.markdown("---")
    st.info("Si tiene problemas para acceder, contacte con un Admin Master.")
