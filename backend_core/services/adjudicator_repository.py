"""
adjudicator_repository.py
Gestión de semillas públicas para el motor determinista de adjudicación.

Tabla usada: ca_adjudication_seeds

Opción A:
- Si NO hay semilla para una sesión, devolvemos None.
- El adjudicator_engine interpreta None como "" y sigue funcionando
  solo con el material determinista técnico (session_id, serie, participantes).
"""

from typing import Optional

from .supabase_client import supabase
from .audit_repository import log_event


SEEDS_TABLE = "ca_adjudication_seeds"


class AdjudicatorRepository:
    # -----------------------------------------------------
    # Obtener semilla pública de una sesión (puede ser None)
    # -----------------------------------------------------
    def get_public_seed_for_session(self, session_id: str) -> Optional[str]:
        """
        Devuelve la semilla pública (public_seed) para una sesión,
        o None si no existe registro.

        IMPORTANTÍSIMO:
        - No lanza excepciones si no hay filas.
        - No usa .single() (que rompe si hay 0 filas).
        """
        try:
            response = (
                supabase
                .table(SEEDS_TABLE)
                .select("public_seed")
                .eq("session_id", session_id)
                .maybe_single()
                .execute()
            )
        except Exception as e:
            # En caso de error con Supabase, registramos y devolvemos None
            log_event(
                action="seed_fetch_error",
                session_id=session_id,
                metadata={"error": str(e)},
            )
            return None

        data = getattr(response, "data", None)

        # Si no hay datos → no hay semilla configurada
        if not data:
            # No logamos como error, porque es un caso normal (semilla opcional)
            return None

        # maybe_single normalmente devuelve un dict, pero por seguridad:
        if isinstance(data, list):
            row = data[0] if data else None
        else:
            row = data

        if not row:
            return None

        return row.get("public_seed")

    # -----------------------------------------------------
    # Crear / actualizar semilla pública para una sesión
    # -----------------------------------------------------
    def set_public_seed_for_session(self, session_id: str, public_seed: str) -> None:
        """
        Crea o actualiza la semilla pública para una sesión concreta.
        Usa upsert por session_id.
        """
        payload = {
            "session_id": session_id,
            "public_seed": public_seed,
        }

        (
            supabase
            .table(SEEDS_TABLE)
            .upsert(payload, on_conflict="session_id")
            .execute()
        )

        log_event(
            action="seed_updated",
            session_id=session_id,
            metadata={"public_seed": public_seed},
        )

    # -----------------------------------------------------
    # Borrar semilla de una sesión
    # -----------------------------------------------------
    def delete_seed_for_session(self, session_id: str) -> None:
        (
            supabase
            .table(SEEDS_TABLE)
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
