import streamlit as st
from backend_core.services.auth_repository import authenticate_user


def login(email: str, password: str) -> bool:
    """
    Intenta autenticar al usuario.
    Si tiene éxito, rellena session_state con datos de usuario.
    """
    auth = authenticate_user(email, password)

    if not auth:
        return False

    st.session_state["user_id"] = auth["user_id"]
    st.session_state["user_email"] = auth["email"]
    # Alias que usábamos antes:
    st.session_state["current_user"] = auth["user_id"]

    return True


def logout():
    """
    Elimina los datos de sesión del usuario actual.
    """
    for key in ["user_id", "user_email", "current_user"]:
        if key in st.session_state:
            del st.session_state[key]


def is_logged_in() -> bool:
    """
    Indica si hay un usuario autenticado.
    """
    return "user_id" in st.session_state and st.session_state["user_id"] is not None
