"""
context.py
Contexto mínimo para el panel en modo desarrollo.

No usa permiso real, solo almacena usuario/org en session_state si hace falta.
"""

import streamlit as st


def get_current_user() -> str | None:
    return st.session_state.get("current_user")


def get_current_org() -> str | None:
    return st.session_state.get("current_org")


def get_current_permissions() -> list[str]:
    # En futuro: cargar de BD / Supabase
    return st.session_state.get("current_permissions", [])
