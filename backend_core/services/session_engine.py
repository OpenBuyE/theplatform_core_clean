# backend_core/services/session_engine.py

from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime

from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event
from backend_core.services.session_repository import (
    get_session_by_id,
    update_session_status,
    mark_session_finished,
    get_next_session_in_series,
)
from backend_core.services.module_engine import get_session_engine
from backend_core.services.module_repository import get_session_module


SESSIONS_TABLE = "ca_sessions"


# ============================================================
# ACTIVACIÓN DE SESIÓN
# ============================================================

def activate_session(session_id: str) -> Dict[str, Any]:
    """
    Activa una sesión (parked → active).
    Invoca la lógica del módulo correspondiente.
    """

    session = get_session_by_id(session_id)
    if not session:
        raise ValueError(f"Session '{session_id}' not found")

    module_engine = get_session_engine(session)

    # Módulo C (prelaunch) bloquea la activación
    # La lógica ya está en on_activate()
    update_session_status(session_id, "active")
    log_event("session_activated", session_id)

    # Delegar en el módulo
    module_engine.on_activate(session)

    return get_session_by_id(session_id)


# ============================================================
# REGISTRO DE PARTICIPANTE
# ============================================================

def on_participant_registered(session_id: str) -> None:
    """
    Llamado cada vez que un participante entra en la sesión.
    Si se completa el aforo, delegamos en el módulo.
    """

    session = get_session_by_id(session_id)
    if not session:
        return

    capacity = session["capacity"]
    pax = session["pax_registered"]

    if pax >= capacity:
        engine = get_session_engine(session)
        log_event("session_full_capacity", session_id)
        engine.on_full_capacity(session)


# ============================================================
# EXPIRACIÓN / TICK
# ============================================================

def heartbeat_tick(session_id: Optional[str] = None) -> None:
    """
    Llamado periódicamente (ej: cron cada minuto).
    Si session_id es None, aplica a todas las sesiones activas.
    """

    if session_id:
        sessions = [get_session_by_id(session_id)]
    else:
        resp = (
            table(SESSIONS_TABLE)
            .select("*")
            .eq("status", "active")
            .execute()
        )
        sessions = resp.data or []

    for session in sessions:
        if not session:
            continue

        engine = get_session_engine(session)

        # Lógica del módulo
        engine.on_tick(session)


# ============================================================
# FINALIZACIÓN EXPRESA DE SESIÓN
# ============================================================

def expire_session(session_id: str) -> None:
    """
    Finaliza una sesión de forma manual (finished = expired)
    y delega al módulo.
    """

    session = get_session_by_id(session_id)
    if not session:
        return

    engine = get_session_engine(session)

    mark_session_finished(session_id, finished_status="expired")
    engine.on_expire(session)

    log_event("session_expired_manual", session_id)


# ============================================================
# ROLLING AUTOMÁTICO SOLO PARA MÓDULO A
# ============================================================

def check_and_trigger_rolling(session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Solo aplica para módulo A (deterministic).
    Activa la siguiente sesión de la serie.
    """

    module = get_session_module(session)
    if module["module_code"] != "A_DETERMINISTIC":
        # Otros módulos NO hacen rolling
        return None

    next_session = get_next_session_in_series(session)
    if not next_session:
        log_event("rolling_no_next_session", session["id"])
        return None

    log_event("rolling_start", session["id"], metadata={"next_session": next_session["id"]})

    return activate_session(next_session["id"])
