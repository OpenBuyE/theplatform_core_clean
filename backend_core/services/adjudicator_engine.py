# backend_core/services/adjudicator_engine.py

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Dict, Optional, List

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
from backend_core.services.module_repository import get_session_module


class AdjudicatorEngine:

    # ============================================================
    #  EJECUTAR ADJUDICACIÓN COMPLETA
    # ============================================================

    def execute_adjudication(self, session_id: str) -> Optional[Dict]:

        session = get_session_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        # Verificar módulo
        module = get_session_module(session)

        if module["module_code"] != "A_DETERMINISTIC":
            raise ValueError(
                f"Este módulo ({module['module_code']}) NO permite adjudicación"
            )

        # Solo adjudicamos sesiones activas
        if session["status"] != "active":
            raise ValueError("Session must be active to adjudicate")

        participants = get_participants_for_session(session_id)
        if len(participants) == 0:
            raise ValueError("No participants registered")

        if len(participants) < session["capacity"]:
            raise ValueError("Aforo incompleto, no se puede adjudicar")

        # ============================================================
        # 1) Construcción de la semilla determinista
        # ============================================================

        seed_data = (
            session_id
            + session["series_id"]
            + str(session["sequence_number"])
            + "".join([p["id"] for p in participants])
        )

        seed_hash = hashlib.sha256(seed_data.encode()).hexdigest()

        # Índice ganador determinista
        winner_index = int(seed_hash, 16) % len(participants)
        winner = participants[winner_index]

        # ============================================================
        # 2) Marcar adjudicatario
        # ============================================================

        mark_awarded(session_id, winner["id"])
        log_event(
            "session_awarded",
            session_id=session_id,
            metadata={
                "winner_participant_id": winner["id"],
                "seed_hash": seed_hash,
                "winner_index": winner_index,
            },
        )

        # ============================================================
        # 3) Finalizar sesión
        # ============================================================

        finish_session(session_id)

        # ============================================================
        # 4) Ejecutar motor contractual
        # ============================================================

        contract_engine.start_contract(session_id)

        # ============================================================
        # 5) Rolling: activar siguiente sesión
        # ============================================================

        session_engine.process_rolling(session)

        return {
            "winner": winner,
            "seed_hash": seed_hash,
            "winner_index": winner_index,
        }


# Instancia global
adjudicator_engine = AdjudicatorEngine()
