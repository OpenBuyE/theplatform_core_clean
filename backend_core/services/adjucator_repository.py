"""
adjudicator_repository.py
Gestiona las semillas públicas de cada sesión
y las operaciones auxiliares del motor determinista.
"""

from datetime import datetime
from typing import Optional, Dict

from .supabase_client import supabase
from .audit_repository import log_event

SEED_TABLE = "session_seeds"


class AdjudicatorRepository:

    # ---------------------------------------------------------
    #  Obtener semilla pública de una sesión
    # ---------------------------------------------------------
    def get_public_seed_for_session(self, session_id: str) -> Optional[str]:
        response = (
            supabase
            .table(SEED_TABLE)
            .select("public_seed")
            .eq("session_id", session_id)
            .maybe_single()
            .execute()
        )

        if response.data:
            return response.data.get("public_seed")

        return None

    # ---------------------------------------------------------
    #  Establecer / reemplazar semilla
    # ---------------------------------------------------------
    def set_public_seed_for_session(self, session_id: str, seed: str) -> None:
        now = datetime.utcnow().isoformat()

        # UPSERT manual: eliminar primero si ya existe
        supabase.table(SEED_TABLE).delete().eq("session_id", session_id).execute()

        # Insertar semilla nueva
        supabase.table(SEED_TABLE).insert({
            "session_id": session_id,
            "public_seed": seed,
            "created_at": now,
            "updated_at": now
        }).execute()

        log_event(
            action="seed_updated",
            session_id=session_id,
            metadata={"public_seed": seed}
        )

    # ---------------------------------------------------------
    #  Borrar semilla pública
    # ---------------------------------------------------------
    def delete_seed_for_session(self, session_id: str) -> None:
        supabase \
            .table(SEED_TABLE) \
            .delete() \
            .eq("session_id", session_id) \
            .execute()

        log_event(
            action="seed_deleted",
            session_id=session_id
        )

    # ---------------------------------------------------------
    #  Obtener registro completo de la semilla (para debug)
    # ---------------------------------------------------------
    def get_seed_record(self, session_id: str) -> Optional[Dict]:
        response = (
            supabase
            .table(SEED_TABLE)
            .select("*")
            .eq("session_id", session_id)
            .maybe_single()
            .execute()
        )
        return response.data


# Instancia global exportable
adjudicator_repository = AdjudicatorRepository()

