import streamlit as st

# ---------------------------------------------------------
#  LAYOUT MINIMAL — SIN CSS, SIN HTML, 100% ESTABLE
# ---------------------------------------------------------

def setup_page():
    """
    Configura la página de manera simple y sin CSS.
    Esta función es segura para Streamlit Cloud.
    """
    st.set_page_config(
        page_title="The Platform — Admin",
        layout="wide"
    )


def render_header():
    """
    Header mínimo. Sin imágenes, sin CSS.
    """
    st.markdown("## 🧩 The Platform — Panel Administrativo")
    st.markdown("---")


def render_sidebar():
    """
    Sidebar mínimo. Esta función NO construye el menú,
    solo sirve como placeholder para mantener estructura.
    """
    st.sidebar.markdown("### Menú")
    # No añadir más contenido aquí por ahora.
    # El menú principal debe definirse siempre
