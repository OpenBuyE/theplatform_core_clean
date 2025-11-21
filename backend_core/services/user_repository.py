"""
user_repository.py
Gestión de usuarios y su pertenencia a organizaciones.
Basado EXCLUSIVAMENTE en supabase_client (sin st.secrets).
"""

from typing import List, Dict, Optional

from .supabase_client import supabase
from .audit_repository import log_event


USER_TABLE = "users"
ORG_USERS_TABLE = "organization_users"


class UserRepository:

    # ---------------------------------------------------------
    #  Obtener usuario por ID
    # ---------------------------------------------------------
    def get_user(self, user_id: str) -> Optional[Dict]:
        resp = (
            supabase
            .table(USER_TABLE)
            .select("*")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        return resp.data

    # ---------------------------------------------------------
    #  Listar todos los usuarios
    # ---------------------------------------------------------
    def list_users(self, limit: int = 200) -> List[Dict]:
        resp = (
            supabase
            .table(USER_TABLE)
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []

    # ---------------------------------------------------------
    #  Listar usuarios en una organización
    # ---------------------------------------------------------
    def list_users_in_org(self, organization_id: str) -> List[Dict]:
        resp = (
            supabase
            .from_(ORG_USERS_TABLE)
            .select("user_id, users(*)")
            .eq("organization_id", organization_id)
            .execute()
        )
        # El formato suele venir como {"user_id": "xx", "users": {...}}
        return [row["users"] for row in resp.data] if resp.data else []

    # ---------------------------------------------------------
    #  Añadir usuario a organización
    # ---------------------------------------------------------
    def add_user_to_org(self, user_id: str, organization_id: str) -> bool:
        resp = (
            supabase
            .table(ORG_USERS_TABLE)
            .insert({
                "user_id": user_id,
                "organization_id": organization_id
            })
            .execute()
        )

        if not resp.data:
            return False

        log_event(
            action="user_added_to_org",
            metadata={"user_id": user_id, "organization_id": organization_id}
        )
        return True


# Instancia global
user_repository = UserRepository()

# Para compatibilidad retro con el panel antiguo
list_users = user_repository.list_users
list_users_in_org = user_repository.list_users_in_org
add_user_to_org = user_repository.add_user_to_org
