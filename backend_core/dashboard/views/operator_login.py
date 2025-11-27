import streamlit as st
import bcrypt
from backend_core.services.supabase_client import table


# ============================================================
# NORMALIZACIÓN
# ============================================================

def normalize_email(e: str) -> str:
    if not e:
        return ""
    return e.strip().lower()


# ============================================================
# FUNCIÓN PARA LEER SIEMPRE result.data
# ============================================================

def safe_execute(query):
    """
    Garantiza que siempre devolvemos una LISTA de filas.
    Supabase en Streamlit Cloud devuelve objects con .data.
    """
    try:
        result = query.execute()
    except Exception as e:
        st.error(f"❌ Error ejecutando consulta Supabase: {e}")
        return []

    # Si tiene .data → usarla
    if hasattr(result, "data"):
        return result.data or []

    # Si es iterable
    if isinstance(result, list):
        return result

    # Fallback
    return []


# ============================================================
# AUTENTICACIÓN ROBUSTA
# ============================================================

def authenticate_operator(email: str, password: str):
    email_norm = normalize_email(email)

    # Leer todos los operadores
    result = safe_execute(
        table("ca_operators").select("*")
    )

    # Nada en tabla
    if not result:
        return None

    # Buscar coincidencia manual
    for op in result:
        email_db = normalize_email(op.get("email", ""))
        active_raw = op.get("active", True)

        is_active = (
            active_raw is True or
            active_raw == "true" or
            active_raw == "True" or
            active_raw == 1
        )

        if email_db == email_norm and is_active:
            stored_hash = op.get("password_hash", "")
            if stored_hash and bcrypt.checkpw(password.encode(), stored_hash.encode()):
                return op

    return None


# ============================================================
# LOGIN UI
# ============================================================

def render_operator_login():
    st.title("🔐 Operator Login")

    st.markdown("### Acceso al Panel Administrativo")

    email = st.text_input("Usuario / Email")
    password = st.text_input("Contraseña", type="password")

    if st.button("Iniciar Sesión"):
        operator = authenticate_operator(email, password)

        if operator:
            st.session_state["operator_id"] = operator["id"]
            st.session_state["email"] = operator["email"]
            st.session_state["full_name"] = operator.get("full_name", "")
            st.session_state["role"] = operator.get("role", "operator")
            st.session_state["allowed_countries"] = operator.get("allowed_countries", ["ES"])
            st.session_state["global_access"] = operator.get("global_access", False)

            st.success("Acceso correcto. Cargando panel…")
            st.experimental_rerun()

        else:
            st.error("❌ Credenciales incorrectas o usuario no activo.")

    st.markdown("---")
    st.info("Si no puede acceder, contacte con Admin Master.")
