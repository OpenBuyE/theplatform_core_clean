"""
adjudicator_repository.py
Repositorio para semillas deterministas de adjudicación.

Tablas usadas:
- ca_adjudication_seeds
    id (uuid)
    session_id (uuid)
    public_seed (text)
    created_at (timestamptz)

Responsabilidad:
- Obtener/guardar la seed pública asociada a una sesión.
- Asegurar siempre respuesta segura para el motor de adjudicación.
"""

from typing import Optional
from datetime import datetime
from .supabase_client import supabase

SEEDS_TABLE = "ca_adjudication_seeds"


class AdjudicationSeedRepository:

    # ---------------------------------------------------------
    # Obtener seed pública de una sesión
    # ---------------------------------------------------------
    def get_public_seed_for_session(self, session_id: str) -> Optional[str]:
        """
        Devuelve la seed pública asociada a una sesión.
        Si no existe → None
        """

        response = (
            supabase
            .table(SEEDS_TABLE)
            .select("public_seed")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
        )

        # Manejo ultra seguro
        if not response or not hasattr(response, "data") or not response.data:
            return None

        row = response.data[0]
        return row.get("public_seed")

    # ---------------------------------------------------------
    # Asignar seed pública a una sesión
    # ---------------------------------------------------------
    def set_public_seed(self, session_id: str, seed: str) -> bool:
        """
        Guarda o actualiza una seed pública para una sesión.
        """

        # Comprobar si ya existe seed para esta sesión
        exists = (

