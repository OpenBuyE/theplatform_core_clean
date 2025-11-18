import streamlit as st


def setup_page():
    st.set_page_config(
        page_title="Compra Abierta – Panel Operativo",
        page_icon="🟢",
        layout="wide"
    )


def render_header():
    st.title("🟢 Compra Abierta – Panel Operativo")
    st.markdown("---")


def render_sidebar():
    st.sidebar.title("Navegación")

    choice = st.sidebar.radio(
        "Selecciona vista:",
        [
            "Parque de Sesiones",
            "Sesiones Activas",
            "Cadenas"
        ]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("© Operador Único — Compra Abierta 3.0")

    return choice
