# backend_core/services/session_repository.py
# ============================================================
# Repositorio profesional de sesiones
# Compatible con todas las vistas del dashboard:
# - Parked / Active / Finished / Scheduled / Standby
# - Session Chains, Engine Monitor, History, Admin Series
# - Active Sessions (participants + adjudication)
# ============================================================

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from backend_core.services.supabase_client import table


# ------------------------------------------------------------
# Helpers internos
# ------------------------------------------------------------

def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _expires_in_5_days() -> str:
    return (datetime.utcnow() + timedelta(days=5)).isoformat()


def _fetch_many(q) -> List[Dict[str, Any]]:
    rows = q.execute()
    return rows or []


def _fetch_one(q) -> Optional[Dict[str, Any]]:
    rows = q.execute()
    if not rows:
        return None
    if isinstance(rows, list):
        return rows[0]
    return rows


# ------------------------------------------------------------
# CREACIÓN / ROLLING
# ------------------------------------------------------------

def create_session(
    product_id: str,
    capacity: int,
    status: str = "parked",
    module_id: Optional[str] = None,
    country: str = "ES",
    organization_id: Optional[str] = None,
    series_id: Optional[str] = None,
) -> str:
    """
    Crea una sesión genérica. Usada internamente y por Admin.
    """
    session_id = str(uuid.uuid4())

    payload = {
        "id": session_id,
        "product_id": product_id,
        "capacity": capacity,
        "pax_registered": 0,
        "status": status,
        "module_id": module_id,
        "country": country,
        "organization_id": organization_id,
        "series_id": series_id,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "expires_at": _expires_in_5_days(),
    }

    table("ca_sessions").insert(payload).execute()
    return session_id


def create_parked_session(
    product_id: str,
    capacity: int,
    country: str = "ES",
    organization_id: Optional[str] = None,
    series_id: Optional[str] = None,
) -> str:
    """
    Conveniencia para Parked Sessions.
    """
    return create_session(
        product_id=product_id,
        capacity=capacity,
        status="parked",
        country=country,
        organization_id=organization_id,
        series_id=series_id,
    )


def create_next_session(previous_session: Dict[str, Any]) -> str:
    """
    Crea la siguiente sesión 'rolling' a partir de una sesión previa.
    Se usa en motores de rolling y session chains.
    """
    return create_session(
        product_id=previous_session["product_id"],
        capacity=previous_session["capacity"],
        status="parked",
        module_id=previous_session.get("module_id"),
        country=previous_session.get("country", "ES"),
        organization_id=previous_session.get("organization_id"),
        series_id=previous_session.get("series_id"),
    )


# ------------------------------------------------------------
# CAMBIO DE ESTADO
# ------------------------------------------------------------

def activate_session(session_id: str):
    """
    parked → active
    """
    (
        table("ca_sessions")
        .update(
            {
                "status": "active",
                "activated_at": _now_iso(),
                "updated_at": _now_iso(),
            }
        )
        .eq("id", session_id)
        .execute()
    )


def finish_session(session_id: str):
    """
    active → finished
    """
    (
        table("ca_sessions")
        .update(
            {
                "status": "finished",
                "finished_at": _now_iso(),
                "updated_at": _now_iso(),
            }
        )
        .eq("id", session_id)
        .execute()
    )


def expire_session(session_id: str):
    """
    marca sesión como expired
    """
    (
        table("ca_sessions")
        .update(
            {
                "status": "expired",
                "expires_at": _now_iso(),
                "updated_at": _now_iso(),
            }
        )
        .eq("id", session_id)
        .execute()
    )


# ------------------------------------------------------------
# LECTURAS BÁSICAS
# ------------------------------------------------------------

def get_session_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Usado por Contract Payment Status y otros.
    """
    q = table("ca_sessions").select("*").eq("id", session_id).single()
    return _fetch_one(q)


def get_sessions(limit: int = 200) -> List[Dict[str, Any]]:
    """
    Sesiones generales, para Operator Dashboard Pro y Engine Monitor.
    """
    q = (
        table("ca_sessions")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
    )
    return _fetch_many(q)


def get_all_sessions() -> List[Dict[str, Any]]:
    """
    Todas las sesiones sin límite (usar con cuidado).
    Usado por algunos monitores globales.
    """
    q = table("ca_sessions").select("*").order("created_at", desc=True)
    return _fetch_many(q)


# ------------------------------------------------------------
# FILTRO POR ESTADO
# ------------------------------------------------------------

def get_parked_sessions(country: Optional[str] = None) -> List[Dict[str, Any]]:
    q = table("ca_sessions").select("*").eq("status", "parked")
    if country:
        q = q.eq("country", country)
    q = q.order("created_at", desc=True)
    return _fetch_many(q)


def get_active_sessions(country: Optional[str] = None) -> List[Dict[str, Any]]:
    q = table("ca_sessions").select("*").eq("status", "active")
    if country:
        q = q.eq("country", country)
    q = q.order("created_at", desc=True)
    return _fetch_many(q)


def get_finished_sessions(country: Optional[str] = None) -> List[Dict[str, Any]]:
    q = table("ca_sessions").select("*").eq("status", "finished")
    if country:
        q = q.eq("country", country)
    q = q.order("finished_at", desc=True)
    return _fetch_many(q)


def get_scheduled_sessions(country: Optional[str] = None) -> List[Dict[str, Any]]:
    q = table("ca_sessions").select("*").eq("status", "scheduled")
    if country:
        q = q.eq("country", country)
    q = q.order("created_at", desc=True)
    return _fetch_many(q)


def get_standby_sessions(country: Optional[str] = None) -> List[Dict[str, Any]]:
    q = table("ca_sessions").select("*").eq("status", "standby")
    if country:
        q = q.eq("country", country)
    q = q.order("created_at", desc=True)
    return _fetch_many(q)


# ------------------------------------------------------------
# SERIES Y CHAINS
# ------------------------------------------------------------

def get_session_series(product_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Devuelve registros de ca_session_series.
    Usado por Admin Series / Session Chains.
    """
    q = table("ca_session_series").select("*")
    if product_id:
        q = q.eq("product_id", product_id)
    q = q.order("created_at", desc=True)
    return _fetch_many(q)


def get_sessions_by_series(series_id: str) -> List[Dict[str, Any]]:
    """
    Todas las sesiones que pertenecen a una serie.
    Utilizado por Session Chains / Admin Series.
    """
    q = (
        table("ca_sessions")
        .select("*")
        .eq("series_id", series_id)
        .order("created_at", desc=True)
    )
    return _fetch_many(q)


def get_next_session_in_series(series_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca la siguiente sesión 'parked' en una serie dada.
    Útil para rolling manual/automático.
    """
    q = (
        table("ca_sessions")
        .select("*")
        .eq("series_id", series_id)
        .eq("status", "parked")
        .order("created_at", asc=True)
        .limit(1)
    )
    return _fetch_one(q)


# ------------------------------------------------------------
# PARTICIPANTES
# ------------------------------------------------------------

def get_participants_for_session(session_id: str) -> List[Dict[str, Any]]:
    """
    Usado por Active Sessions, adjudicator_engine, etc.
    """
    q = (
        table("ca_session_participants")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", asc=True)
    )
    return _fetch_many(q)


def add_test_participant(session_id: str, user_id: Optional[str] = None) -> str:
    """
    Utilidad para Active Sessions: añade un participante dummy.
    Incrementa pax_registered en ca_sessions.
    """
    participant_id = str(uuid.uuid4())
    payload = {
        "id": participant_id,
        "session_id": session_id,
        "user_id": user_id or f"test_user_{participant_id[:8]}",
        "is_awarded": False,
        "created_at": _now_iso(),
    }

    # Insert participante
    table("ca_session_participants").insert(payload).execute()

    # Recontar pax_registered de forma segura
    participants = get_participants_for_session(session_id)
    pax = len(participants)

    table("ca_sessions").update(
        {
            "pax_registered": pax,
            "updated_at": _now_iso(),
        }
    ).eq("id", session_id).execute()

    return participant_id
