import streamlit as st
from backend_core.services.operator_repository import get_operator_by_email

def render_operator_debug():
    st.title("🛠 Operator Debug")

    st.markdown("Esta vista permite verificar si el GlobalAdmin existe y si el backend lo puede leer.")

    st.subheader("Consultar operador por email")

    email = st.text_input("Email del operador", "GlobalAdmin")

    if st.button("Buscar operador"):
        try:
            operator = get_operator_by_email(email)
        except Exception as e:
            st.error(f"Error llamando a get_operator_by_email(): {e}")
            return

        if operator is None:
            st.error("❌ No existe ningún operador con ese email.")
            return

        st.success("✅ Operador encontrado")
        st.json(operator)

    st.markdown("---")
    st.subheader("Estado de sesión Streamlit")

    st.json(st.session_state)
