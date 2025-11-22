"""
adjudicator_repository.py
Repositorio de semillas deterministas para las sesiones (ca_adjudication_seeds).

Responsabilidades:
- Obtener seed pública configurada para una sesión.
- Crear o actualizar seeds.
- Mantener trazabilidad completa.
"""

from typing import Optional, Dict
from .supabase_client import supabase


SEED_TABLE = "ca_adjudication_seeds"


class AdjudicatorRepository:
    # ---------------------------------------------------------
    # Obtener semilla pública para una sesión
    # ---------------------------------------------------------
    def get_public_seed_for_session(self, session_id: str) -> Optional[str]:
        """
        Devuelve la public_seed asociada a una sesión.
        Si no hay registro → devuelve None sin lanzar error.
        """

        # ⚠️ Nunca usar .single() si puede no existir la fila
        response = (
            supabase
            .table(SEED_TABLE)
            .select("public_seed")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
        )

        if not response or not response.data:
            return None

        row = response.data[0]
        return row.get("public_seed")

    # ---------------------------------------------------------
    # Crear seed por primera vez
    # ---------------------------------------------------------
    def create_seed(self, session_id: str, public_seed: str) -> Optional[Dict]:
        response = (
            supabase
            .table(SEED_TABLE)
            .insert({
                "session_id": session_id,
                "public_seed": public_seed,
            })
            .execute()
        )

        return response.data[0] if response.data else None

    # ---------------------------------------------------------
    # Actualizar seed
    # ---------------------------------------------------------
    def update_seed(self, session_id: str, public_seed: str) -> Optional[Dict]:
        response = (
            supabase
            .table(SEED_TABLE)
            .update({"public_seed": public_seed})
            .eq("session_id", session_id)
            .execute()
        )

        return response.data[0] if response.data else None

    # ---------------------------------------------------------
    # Crear o actualizar automáticamente
    # ---------------------------------------------------------
    def upsert_seed(self, session_id: str, public_seed: str) -> Optional[Dict]:
        existing = self.get_public_seed_for_session(session_id)

        if existing is None:
            return self.create_seed(session_id, public_seed)

        return self.update_seed(session_id, public_seed)


# Instancia global
adjudicator_repository = AdjudicatorRepository()
