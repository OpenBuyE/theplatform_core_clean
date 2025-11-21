"""
adjudicator_repository.py
Gestión de semillas deterministas para adjudicación de sesiones.

Tablas mínimas necesarias en Supabase:

    public.session_seeds (
        session_id uuid primary key,
        public_seed text,
        created_at timestamptz default now(),
        updated_at timestamptz
    )
"""

from datetime import datetime
from typing import Optional

from .supabase_client import supabase
from .audit_repository import log_event


class AdjudicatorRepository:
    TABLE_NAME = "session_seeds"

    # ---------------------------------------------------------
    #  Obtener semilla pública de la sesión
    # ---------------------------------------------------------
    def get_public_seed_for_session(self, session_id: str) -> Optional[str]:
        response = (
            supabase.table(self.TABLE_NAME)
            .select("*")
            .eq("session_id", session_id)
            .maybe_single()
            .execute()
        )
        data = response.data
        if not data:
            return None

        log_event(
            action="seed_retrieved",
            session_id=session_id,
            metadata={"public_seed": data.get("public_seed")}
        )
        return data.get("public_seed")

    # ---------------------------------------------------------
    #  Establecer / actualizar semilla pública
    # ---------------------------------------------------------
    def set_public_seed_for_session(self, session_id: str, public_seed: str) -> None:
        now = datetime.utcnow().isoformat()

        existing = (
            supabase.table(self.TABLE_NAME)
            .select("*")
            .eq("session_id", session_id)
            .maybe_single()
            .execute()
        )

        if existing.data:
            (
                supabase.table(self.TABLE_NAME)
                .update({"public_seed": public_seed, "updated_at": now})
                .eq("session_id", session_id)
                .execute()
            )

            log_event(
                action="seed_updated",
                session_id=session_id,
                metadata={
                    "new_public_seed": public_seed,
                    "previous_public_seed": existing.data.get("public_seed"),
                },
            )
        else:
            (
                supabase.table(self.TABLE_NAME)
                .insert(
                    {
                        "session_id": session_id,
                        "public_seed": public_seed,
                        "created_at": now,
                        "updated_at": now,
                    }
                )
                .execute()
            )

            log_event(
                action="seed_created",
                session_id=session_id,
                metadata={"public_seed": public_seed},
            )

    # ---------------------------------------------------------
    #  Eliminar seed (vuelta a solo seed interna)
    # ---------------------------------------------------------
    def delete_seed_for_session(self, session_id: str) -> None:
        (
            supabase.table(self.TABLE_NAME)
            .delete()
            .eq("session_id", session_id)
            .execute()
        )

        log_event(
            action="seed_deleted",
            session_id=session_id,
        )


# Instancia global
adjudicator_repository = AdjudicatorRepository()

        
