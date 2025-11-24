# backend_core/services/adjudicator_engine.py

from __future__ import annotations
from typing import Dict, Any, Optional
import hashlib
import json
from datetime import datetime

from backend_core.services.audit_repository import log_event
from backend_core.services.session_repository import (
    get_session_by_id,
    get_participants_for_session,
    mark_session_finished,
    set_participant_awarded,
)
from backend_core.services.module_repository import get_session_module
from backend_core.services.session_engine import check_and_trigger_rolling
from backend_core.services.contract_engine import contract_engine


class AdjudicatorEngine:
    """
    Motor determinista de adjudicación.
    Ahora integrado con el sistema de módulos:
    - Solo adjudica si module_code = A_DETERMINISTIC
    """

    # ------------------------------------------------------
    # Punto de entrada principal
    # ------------------------------------------------------
    def execute_adjudication(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Ejecuta adjudicación determinista:
        - Solo si módulo = A_DETERMINISTIC
        - No re-ejecuta adjudicación si la sesión no está active o ya finished
        """

        session = get_session_by_id(session_id)
        if not session:
            raise ValueError(f"Session '{session_id}' not found")

        # --------------------------------------------------
        # VALIDAR MÓDULO
        # --------------------------------------------------
        module = get_session_module(session)
        if module["module_code"] != "A_DETERMINISTIC":
            log_event(
                "adjudication_blocked_by_module",
                session_id,
                metadata={"module": module["module_code"]},
            )
            return None  # adjudicación bloqueada

        if session["status"] != "active":
            log_event("adjudication_invalid_status", session_id, metadata={"status": session["status"]})
            return None

        # --------------------------------------------------
        # REQUERIR LISTA DE PARTICIPANTES
        # --------------------------------------------------
        participants = get_participants_for_session(session_id)

        if not participants or len(participants) < session["capacity"]:
            log_event(
                "adjudication_blocked_insufficient_pax",
                session_id,
                metadata={"pax": len(participants), "capacity": session["capacity"]},
            )
            return None

        # --------------------------------------------------
        # CONSTRUIR SEED DETERMINISTA
        # --------------------------------------------------
        adjudication_seed = self._build_deterministic_seed(session, participants)
        adjudication_hash = hashlib.sha256(adjudication_seed.encode()).hexdigest()

        index = int(adjudication_hash, 16) % len(participants)
        awarded = participants[index]

        # --------------------------------------------------
        # MARCAR PARTICIPANTE COMO ADJUDICADO
        # --------------------------------------------------
        set_participant_awarded(awarded["id"])

        mark_session_finished(session_id, finished_status="finished")

        log_event(
            "session_adjudicated",
            session_id,
            metadata={
                "awarded_participant": awarded["id"],
                "hash": adjudication_hash,
                "used_seed": adjudication_seed,
            },
        )

        # --------------------------------------------------
        # TRIGGER CONTRACT ENGINE (solo módulo A)
        # --------------------------------------------------
        contract_engine.on_session_awarded(session_id, awarded["id"])

        # --------------------------------------------------
        # ROLLING (solo módulo A)
        # --------------------------------------------------
        return check_and_trigger_rolling(session)

    # ------------------------------------------------------
    # Construcción de la semilla determinista
    # ------------------------------------------------------
    def _build_deterministic_seed(self, session: Dict[str, Any], participants: list) -> str:
        """
        Construye la semilla determinista oficial:
        SHA256(session_id + series_id + sequence_number + participantes + public_seed)
        """

        participants_sorted = sorted([p["id"] for p in participants])

        data = {
            "session_id": session["id"],
            "series_id": session["series_id"],
            "sequence_number": session["sequence_number"],
            "participants": participants_sorted,
            "public_seed": session.get("public_seed") or "",
        }

        return json.dumps(data, sort_keys=True)


adjudicator_engine = AdjudicatorEngine()
