"""
user_repository.py
Gestión de usuarios dentro de organizaciones para Compra Abierta.

Este repositorio:
- Lista usuarios globales
- Lista usuarios por organización
- Añade usuario a una organización
- Usa supabase_client.py (NO st.secrets)
"""

from typing import List, Dict, Optional
from .supabase_client import supabase
from .audit_repository import log_event

USER_TABLE = "users"
ORG_USERS_TABLE = "organization_users"


class UserRepository:

    # ---------------------------------------------------------
    # Listar todos los usuarios
    # ---------------------------------------------------------
    def list_users(self, limit: int = 200) -> List[Dict]:
        response = (
            supabase.table(USER_TABLE)
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    # ---------------------------------------------------------
    # Listar usuarios dentro de una organización
    # ---------------------------------------------------------
    def list_users_in_org(self, organization_id: str) -> List[Dict]:
        response = (
            supabase.table(ORG_USERS_TABLE)
            .select("*, users(*)")
            .eq("organization_id", organization_id)
            .execute()
        )
        return response.data or []

    # ---------------------------------------------------------
    # Añadir usuario a organización
    # ---------------------------------------------------------
    def add_user_to_org(self, user_id: str, organization_id: str) -> Optional[Dict]:
        response = (
            supabase.table(ORG_USERS_TABLE)
            .insert({
                "organization_id": organization_id,
                "user_id": user_id
            })
            .execute()
        )

        if not response.data:
            log_event(
                action="user_add_to_org_error",
                metadata={"user_id": user_id, "organization_id": organization_id}
            )
            return None

        log_event(
            action="user_added_to_org",
            metadata={"user_id": user_id, "organization_id": organization_id}
        )

        return response.data[0]


# Instancia global exportable
user_repository = UserRepository()
