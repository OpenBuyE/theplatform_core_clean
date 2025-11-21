"""
acl.py
Capa de permisos simplificada para desarrollo.

require_org y require_permission son NO-OPs (no bloquean nada).
En producción se deberá conectar con permission_repository y contexto real.
"""

from functools import wraps
import streamlit as st

from .context import get_current_org, get_current_permissions


def require_org(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # En dev no bloqueamos; en el futuro podríamos comprobar org
        return func(*args, **kwargs)

    return wrapper


def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # En dev no bloqueamos; en el futuro:
            # perms = get_current_permissions()
            # if permission not in perms: ...
            return func(*args, **kwargs)

        return wrapper

    return decorator
