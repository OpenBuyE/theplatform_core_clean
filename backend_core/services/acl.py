import streamlit as st
from functools import wraps
from backend_core.services.context import (
    get_current_user,
    get_current_org,
    get_current_permissions,
)


def require_user(func):
    """Bloquea la función si no hay usuario identificado."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not get_current_user():
            st.error("⛔ Debes iniciar sesión para acceder a esta sección.")
            return
        return func(*args, **kwargs)
    return wrapper


def require_org(func):
    """Bloquea la función si no hay organización seleccionada."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not get_current_org():
            st.error("⛔ Debes seleccionar una organización para continuar.")
            return
        return func(*args, **kwargs)
    return wrapper


def require_permission(permission_code: str):
    """
    Bloquea la función si el usuario no tiene un permiso concreto.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            perms = get_current_permissions()
            if permission_code not in perms:
                st.error("⛔ No tienes permiso para realizar esta acción.")
                return
            return func(*args, **kwargs)
        return wrapper
    return decorator
