# backend_core/services/module_engine.py

from __future__ import annotations
from typing import Dict, Any, Optional

from datetime import datetime, timedelta

from backend_core.services.audit_repository import log_event
from backend_core.services.module_repository import get_session_module
from backend_core.services.session_repository import (
    mark_session_finished,
    update_session_status,
    get_session_by_id,
)
from backend_core.services.adjudicator_engine import adjudicator_engine


# ============================================================
# BASE MODULE ENGINE
# ============================================================

class BaseModuleEngine:
    """
    Clase base para todos los módulos de sesión.
    Define la interfaz que todos deben implementar.
    """

    module_code: str = ""
    name: str = ""

    # -----------------------------------------
    # Reglas al activar una sesión
    # -----------------------------------------
    def on_activate(self, session: Dict[str, Any]) -> None:
        """
        Se ejecuta cuando una sesión pasa a estado 'active'.
        """
        pass

    # -----------------------------------------
    # Reglas de transición (cron / heartbeat)
    # -----------------------------------------
    def on_tick(self, session: Dict[str, Any]) -> None:
        """
        Se ejecuta en procesos periódicos (expiración, validaciones).
        """
        pass

    # -----------------------------------------
    # Reglas cuando el aforo se completa
    # -----------------------------------------
    def on_full_capacity(self, session: Dict[str, Any]) -> None:
        """
        Aforo completo -> se decide si adjudica, expira o no hace nada.
        """
        pass

    # -----------------------------------------
    # Reglas de adjudicación
    # -----------------------------------------
    def on_adjudication(self, session: Dict[str, Any]) -> None:
        """
        Solo para módulos que adjudican (A).
        """
        pass

    # -----------------------------------------
    # Reglas cuando la sesión expira
    # -----------------------------------------
    def on_expire(self, session: Dict[str, Any]) -> None:
        """
        Se ejecuta cuando expires_at < now.
        """
        pass


# ============================================================
# MODULE A — ESTÁNDAR DETERMINISTA
# ============================================================

class ModuleA_Deterministic(BaseModuleEngine):
    module_code = "A_DETERMINISTIC"
    name = "Sesión Estándar Determinista"

    def on_activate(self, session: Dict[str, Any]) -> None:
        log_event("module_a_on_activate", session["id"], metadata={"info": "Sesión activada bajo módulo A"})

    def on_full_capacity(self, session: Dict[str, Any]) -> None:
        log_event("module_a_aforo_completo", session["id"])
        adjudicator_engine.execute_adjudication(session["id"])

    def on_adjudication(self, session: Dict[str, Any]) -> None:
        log_event("module_a_adjudication_trigger", session["id"])

    def on_tick(self, session: Dict[str, Any]) -> None:
        # Validar expiración
        if session.get("expires_at"):
            now = datetime.utcnow()
            expires_at = session["expires_at"]
            if now > expires_at and session["status"] == "active":
                log_event("module_a_expired_auto", session["id"], metadata={"reason": "expiration"})
                mark_session_finished(session["id"], finished_status="expired")

    def on_expire(self, session: Dict[str, Any]) -> None:
        log_event("module_a_manual_expire", session["id"])


# ============================================================
# MODULE B — AUTO EXPIRE
# ============================================================

class ModuleB_AutoExpire(BaseModuleEngine):
    module_code = "B_AUTO_EXPIRE"
    name = "Sesión Auto-Expire"

    def on_activate(self, session: Dict[str, Any]) -> None:
        log_event("module_b_on_activate", session["id"])

    def on_full_capacity(self, session: Dict[str, Any]) -> None:
        """
        En módulo B NO adjudicamos.
        Simplemente marcamos como finished.
        """
        log_event("module_b_aforo_completo", session["id"])
        mark_session_finished(session["id"], finished_status="finished")

    def on_tick(self, session: Dict[str, Any]) -> None:
        now = datetime.utcnow()

        if session.get("expires_at") and now > session["expires_at"]:
            log_event("module_b_expired_auto", session["id"])
            mark_session_finished(session["id"], finished_status="expired")

    def on_expire(self, session: Dict[str, Any]) -> None:
        log_event("module_b_manual_expire", session["id"])


# ============================================================
# MODULE C — PRELAUNCH
# ============================================================

class ModuleC_Prelaunch(BaseModuleEngine):
    module_code = "C_PRELAUNCH"
    name = "Prelaunch"

    def on_activate(self, session: Dict[str, Any]) -> None:
        """
        Las sesiones prelaunch NO deben poder ser activadas.
        """
        log_event("module_c_activation_blocked", session["id"], metadata={"error": "Prelaunch no puede activarse"})
        update_session_status(session["id"], "parked")

    def on_full_capacity(self, session: Dict[str, Any]) -> None:
        """
        Módulo C no registra participantes: aforo es irrelevante.
        """
        log_event("module_c_full_capacity_ignored", session["id"])

    def on_tick(self, session: Dict[str, Any]) -> None:
        """
        Puede enviar notificaciones internas (en el futuro).
        """
        pass

    def on_expire(self, session: Dict[str, Any]) -> None:
        log_event("module_c_manual_expire", session["id"])


# ============================================================
# MODULE ENGINE REGISTRY
# ============================================================

MODULE_ENGINES: Dict[str, BaseModuleEngine] = {
    "A_DETERMINISTIC": ModuleA_Deterministic(),
    "B_AUTO_EXPIRE": ModuleB_AutoExpire(),
    "C_PRELAUNCH": ModuleC_Prelaunch(),
}


def get_session_engine(session: Dict[str, Any]) -> BaseModuleEngine:
    """
    Retorna el módulo correcto según session.module_code.
    """
    module = get_session_module(session)
    code = module["module_code"]
    return MODULE_ENGINES.get(code, MODULE_ENGINES["A_DETERMINISTIC"])
