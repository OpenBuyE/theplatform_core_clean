import streamlit as st

from .ui.layout import (
    setup_page,
    render_header,
    render_sidebar
)

from .views.park_sessions import render_park_sessions
from .views.active_sessions import render_active_sessions
from .views.chains import render_chains

def main():
    setup_page()
    render_header()
    choice = render_sidebar()

    if choice == "Parque de Sesiones":
        render_park_sessions()
    elif choice == "Sesiones Activas":
        render_active_sessions()
    elif choice == "Cadenas":
        render_chains()

if __name__ == "__main__":
    main()

