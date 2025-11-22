"""
adjudicator_repository.py
Repositorio para semillas deterministas de adjudicación.

Tabla: ca_adjudication_seeds
Campos:
- session_id (UUID, PK)
- public_seed (TEXT, nullable)
- created_at (TIMESTAMP)
"""

from typing import Optional, Dict, Any
from datetime import datetime

from .supabase_client import supabase
from .audit_repository import log_event


SEED_TABLE = "ca_adjudication_seeds"


class AdjudicatorRepository:
    # ---------------------------------------------------------
    #  Obtener seed pública para una sesión
    # ---------------------------------------------------------
    def get_public_seed_for_session(self, session_id: str) -> Optional[str]:
        response = (
            supabase
            .table(SEED_TABLE)
            .select("public_seed")
            .eq("session_id", session_id)
            .single()
            .execute()
        )

        if not response or not response.data:
            return None

        return response.data.get("public_seed")

    # ---------------------------------------------------------
    #  Establecer / actualizar seed pública
    # ---------------------------------------------------------
    def set_public_seed(self, session_id: str, seed: str) -> None:
        now = datetime.utcnow().isoformat()

        # Upsert (insert or update)
        response = (
            supabase
            .table(SEED_TABLE)
            .upsert({
                "session_id": session_id,
                "public_seed": seed,
                "created_at": now,
            })
            .execute()
        )

        log_event(
            action="public_seed_set",
            session_id=session_id,
            metadata={"seed": seed}
        )

    # ---------------------------------------------------------
    #  Verificar si existe entrada para una sesión
    # ---------------------------------------------------------
    def seed_exists(self, session_id: str) -> bool:
        response = (
            supabase
            .table(SEED_TABLE)
            .select("session_id")
            .eq("session_id", session_id)
            .execute()
        )

        return bool(response.data)

    # ---------------------------------------------------------
    #  Crear entrada vacía si no existe
    # ---------------------------------------------------------
    def ensure_seed_record(self, session_id: str) -> None:
        if self.seed_exists(session_id):
            return

        now = datetime.utcnow().isoformat()

        supabase.table(SEED_TABLE).insert({
            "session_id": session_id,
            "public_seed": None,
            "created_at": now,
        }).execute()

        log_event(
            action="seed_record_created",
            session_id=session_id,
        )


# Instancia global
adjudicator_repository = AdjudicatorRepository()
