"""
permission_repository.py
Gestión simplificada de permisos.

En esta versión:
- No usamos st.secrets.
- No usamos SERVICE_ROLE.
- Obtenemos permisos desde tabla Supabase.
"""

from typing import List, Dict

from .supabase_client import supabase


PERMISSION_TABLE = "permissions"
ROLE_PERMISSION_TABLE = "role_permissions"
USER_ROLE_TABLE = "user_roles"


class PermissionRepository:

    # ---------------------------------------------------------
    #  Obtener roles que tiene un usuario
    # ---------------------------------------------------------
    def get_roles_for_user(self, user_id: str) -> List[Dict]:
        resp = (
            supabase
            .from_(USER_ROLE_TABLE)
            .select("role_id")
            .eq("user_id", user_id)
            .execute()
        )
        return resp.data or []

    # ---------------------------------------------------------
    #  Obtener permisos agregados para un usuario
    # ---------------------------------------------------------
    def get_user_permissions(self, user_id: str) -> List[str]:
        # Roles del usuario
        roles = self.get_roles_for_user(user_id)
        role_ids = [r["role_id"] for r in roles]

        if not role_ids:
            return []

        # Buscar permisos asociados a esos roles
        resp = (
            supabase
            .from_(ROLE_PERMISSION_TABLE)
            .select("permission_id, permissions(name)")
            .in_("role_id", role_ids)
            .execute()
        )

        if not resp.data:
            return []

        return [row["permissions"]["name"] for row in resp.data]

    # ---------------------------------------------------------
    #  Verificar si usuario tiene un permiso concreto
    # ---------------------------------------------------------
    def user_has_permission(self, user_id: str, permission_name: str) -> bool:
        return permission_name in self.get_user_permissions(user_id)


permission_repository = PermissionRepository()

# compatibilidad retro
get_user_permissions = permission_repository.get_user_permissions
user_has_permission = permission_repository.user_has_permission
