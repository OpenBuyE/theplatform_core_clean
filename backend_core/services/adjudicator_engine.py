# backend_core/services/adjudicator_engine.py

from __future__ import annotations

import hashlib
from typing import Dict, Any, List

from backend_core.services.audit_repository import log_event
from backend_core.services.session_repository import (
    get_session_by_id,
    finish_session,
)
from backend_core.services.participant_repository import (
    get_participants_for_session,
    mark_awarded,
)
from backend_core.services.session_engine import session_engine
from backend_core.services.contract_engine import contract_engine
from backend_core.services.module_repository import get_module_for_session


class AdjudicatorEngine:
    """
    Motor de adjudicación determinista simplificado:
    - No usa todavía tabla de seeds (para no romper nada).
    - Usa session_id + ids de participantes para construir el hash.
    """

    def _validate_ready(self, session: Dict[str, Any], participants: List[Dict[str, Any]]):
        if session["status"] != "active":
            raise ValueError("La sesión no está activa.")

        if not participants:
            raise ValueError("La sesión no tiene participantes.")

        if session["pax_registered"] < session["capacity"]:
            raise ValueError("El aforo no está completo.")

    def run_adjudication(self, session_id: str) -> Dict[str, Any]:
        session = get_session_by_id(session_id)
        if not session:
            raise ValueError("Sesión no encontrada.")

        participants = get_participants_for_session(session_id)

        # Validaciones básicas
        self._validate_ready(session, participants)

        # Comprobar módulo (solo módulos deterministas deberían adjudicar)
        module = get_module_for_session(session_id)
        if module and module.get("module_status") == "cancelled":
            raise ValueError("El módulo está cancelado; no se puede adjudicar.")

        # Construir base determinista (sin seed por ahora)
        base = session_id + "".join(p["id"] for p in participants)
        digest = hashlib.sha256(base.encode()).hexdigest()
        index = int(digest, 16) % len(participants)

        winner = participants[index]

        # Marcar adjudicatario
        mark_awarded(winner["id"])

        # Cerrar sesión
        finish_session(session_id)

        log_event(
            "session_adjudicated",
            session_id=session_id,
            metadata={
                "winner_participant_id": winner["id"],
                "hash": digest,
                "winner_index": index,
            },
        )

        # Lanzar flujo contractual
        contract_engine.start_contract_flow(session_id)

        # Rolling
        session_engine.run_rolling_if_needed(session_id)

        return {
            "session_id": session_id,
            "winner_participant_id": winner["id"],
            "hash": digest,
            "winner_index": index,
        }


# Instancia global
adjudicator_engine = AdjudicatorEngine()
