"""
permission_repository.py
Gestión de permisos de usuario basada en tablas de Supabase.
"""

from .supabase_client import supabase


PERMISSIONS_TABLE = "user_permissions"


def get_user_permissions(user_id: str) -> list[str]:
    """
    Devuelve lista de permisos asociados a un usuario.
    """
    if not user_id:
        return []

    response = (
        supabase
        .table(PERMISSIONS_TABLE)
        .select("permission")
        .eq("user_id", user_id)
        .execute()
    )

    if not response.data:
        return []

    return [row["permission"] for row in response.data]
