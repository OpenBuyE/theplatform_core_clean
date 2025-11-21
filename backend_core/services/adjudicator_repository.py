"""
adjudicator_repository.py
Repositorio para gestión de semillas públicas y metadatos
del motor determinista de adjudicación.
"""

from datetime import datetime
from typing import Optional, Dict

from .supabase_client import supabase
from .audit_repository import log_event


SEEDS_TABLE = "session_seeds"


class AdjudicatorRepository:

    # ---------------------------------------------------------
    # Obtener seed pública asociada a una sesión
    # ---------------------------------------------------------
    def get_public_seed_for_session(self, session_id: str) -> Optional[str]:
        response = (
            supabase
            .table(SEEDS_TABLE)
            .select("public_seed")
            .eq("session_id", session_id)
            .maybe_single()
            .execute()
        )

        if not response.data:
            return None

        return response.data.get("public_seed")

    # ---------------------------------------------------------
    # Establecer/actualizar seed pública
    # ---------------------------------------------------------
    def set_public_seed_for_session(self, session_id: str, seed: str) -> None:
        now = datetime.utcnow().isoformat()

        # UPSERT manual: borrar y volver a insertar →
        # evita problemas con maybe_single()
        supabase.table(SEEDS_TABLE).delete().eq("session_id", session_id).execute()

        supabase.table(SEEDS_TABLE).insert({
            "session_id": session_id,
            "public_seed": seed,
            "created_at": now,
            "updated_at": now
        }).execute()

        log_event(
            action="public_seed_set",
            session_id=session_id,
            metadata={"seed": seed}
        )

    # ---------------------------------------------------------
    # Eliminar seed (debug / tests / reset)
    # ---------------------------------------------------------
    def delete_seed_for_session(self, session_id: str) -> None:
        supabase.table(SEEDS_TABLE).delete().eq("session_id", session_id).execute()

        log_event(
            action="public_seed_deleted",
            session_id=session_id
        )


# Instancia global
adjudicator_repository = AdjudicatorRepository()

