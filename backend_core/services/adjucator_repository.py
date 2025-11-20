"""
adjudicator_repository.py
Gestión de semillas deterministas para adjudicación de sesiones.

Este módulo permite:
- Establecer una semilla pública para una sesión concreta
- Obtener la semilla pública de una sesión
- Registrar auditoría cada vez que una seed se crea, cambia o se solicita
- Preparar el backend para integrar un oráculo externo de seeds

Tablas mínimas necesarias en Supabase:

    public.session_seeds (
        session_id uuid primary key,
        public_seed text,
        created_at timestamptz default now(),
        updated_at timestamptz
    )

Si la tabla no existe en tu BD, puedo generarte el script SQL.
"""

from datetime import datetime
from .supabase_client import supabase
from .audit_repository import log_event


class AdjudicatorRepository:

    TABLE_NAME = "session_seeds"

    # ---------------------------------------------------------
    #  Obtener semilla pública de la sesión
    # ---------------------------------------------------------
    @staticmethod
    def get_public_seed_for_session(session_id: str) -> str | None:
        """
        Devuelve la seed pública asociada a una sesión.
        Si no existe, devuelve None.
        """

        response = (
            supabase
            .table(AdjudicatorRepository.TABLE_NAME)
            .select("*")
            .eq("session_id", session_id)
            .maybe_single()
            .execute()
        )

        data = response.data
        if not data:
            # Registrar en auditoría que la sesión no tiene seed
            log_event(
                action="seed_not_found",
                session_id=session_id,
                metadata={"repository": "adjudicator_repository"}
            )
            return None

        # Registrar que la seed ha sido consultada
        log_event(
            action="seed_retrieved",
            session_id=session_id,
            metadata={"public_seed": data.get("public_seed")}
        )

        return data.get("public_seed")

    # ---------------------------------------------------------
    #  Establecer una semilla pública
    # ---------------------------------------------------------
    @staticmethod
    def set_public_seed_for_session(session_id: str, public_seed: str) -> None:
        """
        Establece o actualiza la seed pública de una sesión.
        """

        now = datetime.utcnow().isoformat()

        # Comprobar si ya existe
        existing = (
            supabase
            .table(AdjudicatorRepository.TABLE_NAME)
            .select("*")
            .eq("session_id", session_id)
            .maybe_single()
            .execute()
        )

        if existing.data:
            # Actualizar
            (
                supabase
                .table(AdjudicatorRepository.TABLE_NAME)
                .update({
                    "public_seed": public_seed,
                    "updated_at": now
                })
                .eq("session_id", session_id)
                .execute()
            )

            log_event(
                action="seed_updated",
                session_id=session_id,
                metadata={
                    "new_public_seed": public_seed,
                    "previous_public_seed": existing.data.get("public_seed")
                }
            )

        else:
            # Insertar nueva
            (
                supabase
                .table(AdjudicatorRepository.TABLE_NAME)
                .insert({
                    "session_id": session_id,
                    "public_seed": public_seed,
                    "created_at": now
                })
                .execute()
            )

            log_event(
                action="seed_created",
                session_id=session_id,
                metadata={"public_seed": public_seed}
            )

    # ---------------------------------------------------------
    #  Integración futura con oráculo externo (placeholder)
    # ---------------------------------------------------------
    @staticmethod
    def fetch_external_seed(source_url: str) -> str | None:
        """
        Método placeholder para integración futura con oráculos externos.
        Devolverá una seed obtenida desde un endpoint público verificable.

        Por ahora no implementamos la llamada externa (no permitido en backend actual),
        pero dejamos la estructura para añadirla cuando toque.
        """

        # TODO: Implementar cuando se autorice fetch externo
        log_event(
            action="external_seed_requested",
            session_id=None,
            metadata={"source": source_url}
        )

        return None

    # ---------------------------------------------------------
    #  Helper: eliminar una seed (solo para debugging / desarrollo)
    # ---------------------------------------------------------
    @staticmethod
    def delete_seed_for_session(session_id: str) -> None:
        """
        Elimina la seed de una sesión.
        Útil para pruebas o reseteos.
        """

        (
            supabase
            .table(AdjudicatorRepository.TABLE_NAME)
            .delete()
            .eq("session_id", session_id)
            .execute()
        )

        log_event(
            action="seed_deleted",
            session_id=session_id
        )


# Instancia única exportable
adjudicator_repository = AdjudicatorRepository()
