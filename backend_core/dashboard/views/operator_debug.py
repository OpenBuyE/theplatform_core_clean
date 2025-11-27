import streamlit as st
from backend_core.services.operator_repository import get_operator_by_email

def render_operator_debug():
    st.title("Operator Debug Tool")

    email = st.text_input("Email del operador")

    if st.button("Buscar"):
        try:
            op = get_operator_by_email(email)
            if not op:
                st.error("No encontrado.")
            else:
                st.json(op)
        except Exception as e:
            st.error(f"Error: {e}")
