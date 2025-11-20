"""
permission_repository.py
Sistema mínimo de permisos local para Compra Abierta.

Este módulo reemplaza la dependencia de Supabase SERVICE ROLE
y elimina el uso de st.secrets["SUPABASE_SERVICE_ROLE"].
"""

# ❗ NO USAMOS SUPABASE AQUÍ — evita errores de entorno
# El sistema operativo es local y de pruebas.

LOCAL_DEFAULT_PERMISSIONS = {
    "admin": ["view", "manage", "activate", "audit"],
    "operator": ["view", "activate"],
    "viewer": ["view"],
}


def get_user_permissions(user_id: str) -> list:
    # Por ahora asignamos permiso "admin" a todos
    # para evitar errores en el panel
    return LOCAL_DEFAULT_PERMISSIONS["admin"]
