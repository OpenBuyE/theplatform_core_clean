# backend_core/services/session_engine.py

from __future__ import annotations

from datetime import datetime
from typing import Optional

from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event
from backend_core.services.session_repository import (
    get_session_by_id,
    activate_session,
    finish_session,
    get_next_session_in_series,
)
from backend_core.services.module_repository import get_session_module
from backend_core.services.contract_engine import contract_engine


SESSIONS_TABLE = "ca_sessions"


class SessionEngine:

    # ============================================================
    # 1) PROCESAMIENTO DE EXPIRACIONES
    # ============================================================

    def process_expiration(self, session: dict) -> Optional[dict]:
        """
        Verifica y aplica expiración de sesiones para módulos B y C.
        """

        module = get_session_module(session)

        if module["module_code"] not in ["B_AUTO_EXPIRE"]:
            return session  # Solo el módulo B expira automático

        expires_at = session.get("expires_at")
        if not expires_at:
            return session

        now = datetime.utcnow()
        exp_dt = (
            expires_at if isinstance(expires_at, datetime) else datetime.fromisoformat(expires_at)
        )

        if now >= exp_dt and session["status"] == "active":
            # finalizar sesión
            finished = finish_session(session["id"])

            log_event(
                "session_auto_expired",
                session_id=session["id"],
                metadata={"expires_at": expires_at},
            )

            return finished

        return session

    # ============================================================
    # 2) ACTIVACIÓN PROGRAMADA
    # ============================================================

    def activate_if_needed(self, session_id: str) -> dict:
        """
        Activa una sesión parked si cumple condiciones.
        Solo módulos A y B pueden activarse.
        """

        session = get_session_by_id(session_id)
        module = get_session_module(session)

        if module["module_code"] in ["C_PRELAUNCH"]:
            # No se activa automáticamente
            return session

        if session["status"] == "parked":
            return activate_session(session_id)

        return session

    # ============================================================
    # 3) ROLLING
    # ============================================================

    def process_rolling(self, session: dict) -> Optional[dict]:
        """
        Si una sesión termina (finished), activa la siguiente en su serie.
        Aplica SOLO a módulo A (determinista).
        """

        module = get_session_module(session)

        if module["module_code"] != "A_DETERMINISTIC":
            return None

        # Necesitamos siguiente sesión en la serie
        next_sess = get_next_session_in_series(
            session["series_id"], session["sequence_number"]
        )

        if not next_sess:
            return None  # No hay más sesiones en la serie

        # Activamos la siguiente
        activated = activate_session(next_sess["id"])

        log_event(
            "rolling_session_activated",
            session_id=activated["id"],
            metadata={
                "previous_session_id": session["id"],
                "series_id": session["series_id"],
            },
        )

        return activated

    # ============================================================
    # 4) OPERACIÓN DE MÓDULOS — PROCESO GENERAL
    # ============================================================

    def process_session(self, session_id: str) -> dict:
        """
        Punto de entrada general para procesar una sesión:
        - expiración
        - activación
        - rolling
        """

        session = get_session_by_id(session_id)
        if not session:
            raise ValueError("Session not found")

        module = get_session_module(session)

        # Expiración solo aplica a Módulo B
        if module["module_code"] == "B_AUTO_EXPIRE":
            session = self.process_expiration(session)

        return session


# Instancia global
session_engine = SessionEngine()
