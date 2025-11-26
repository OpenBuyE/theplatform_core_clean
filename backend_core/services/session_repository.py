import typing as t
from datetime import datetime, timedelta

from backend_core.services.supabase_client import table
from backend_core.services.operator_repository import (
    get_operator_allowed_countries,
    ensure_country_filter,
)

# =========================================================
# HELPERS INTERNOS
# =========================================================

def _safe_data(resp):
    """Compatibilidad con posibles formatos del wrapper REST."""
    if hasattr(resp, "data"):
        return resp.data
    return resp.get("data")


# =========================================================
#     SESSION REPOSITORY — ACCESO FILTRADO POR PAÍS
# =========================================================


# -----------------------------
# GETTERS PRINCIPALES
# -----------------------------

def get_session_by_id(session_id: str) -> t.Optional[dict]:
    resp = (
        table("ca_sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )
    return _safe_data(resp)


def get_sessions(operator_id: str) -> t.List[dict]:
    allowed = get_operator_allowed_countries(operator_id)

    qb = table("ca_sessions").select("*")
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_data(resp) or []


def get_parked_sessions(operator_id: str) -> t.List[dict]:
    allowed = get_operator_allowed_countries(operator_id)

    qb = (
        table("ca_sessions")
        .select("*")
        .eq("status", "parked")
    )
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_data(resp) or []


def get_active_sessions(operator_id: str) -> t.List[dict]:
    allowed = get_operator_allowed_countries(operator_id)

    qb = (
        table("ca_sessions")
        .select("*")
        .eq("status", "active")
    )
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_data(resp) or []


def get_finished_sessions(operator_id: str) -> t.List[dict]:
    allowed = get_operator_allowed_countries(operator_id)

    qb = (
        table("ca_sessions")
        .select("*")
        .eq("status", "finished")
    )
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_data(resp) or []


def get_expired_sessions(operator_id: str) -> t.List[dict]:
    allowed = get_operator_allowed_countries(operator_id)

    qb = (
        table("ca_sessions")
        .select("*")
        .eq("status", "expired")
    )
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_data(resp) or []


# -----------------------------
# PARTICIPANTS
# -----------------------------

def get_participants_for_session(session_id: str) -> t.List[dict]:
    resp = (
        table("ca_session_participants")
        .select("*")
        .eq("session_id", session_id)
        .execute()
    )
    return _safe_data(resp) or []


# -----------------------------
# NEXT SESSION IN SERIES (ROLLING)
# -----------------------------

def get_next_session_in_series(series_id: str) -> t.Optional[dict]:
    resp = (
        table("ca_sessions")
        .select("*")
        .eq("series_id", series_id)
        .eq("status", "parked")
        .order("created_at", ascending=True)
        .execute()
    )

    rows = _safe_data(resp) or []
    return rows[0] if rows else None


# =========================================================
#     CREATE / UPDATE / STATE CHANGES
# =========================================================


def create_session(
    product_id: str,
    module_id: str,
    series_id: str,
    aforo: int,
    country_code: str,
) -> dict:
    """
    Crea una sesión nueva (rolling-ready).
    """
    payload = {
        "product_id": product_id,
        "module_id": module_id,
        "series_id": series_id,
        "aforo": aforo,
        "status": "parked",
        "country_code": country_code,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(days=5)).isoformat(),
    }

    resp = table("ca_sessions").insert(payload).execute()
    return _safe_data(resp)


def activate_session(session_id: str) -> dict:
    """
    Cambia estado a 'active'.
    """
    resp = (
        table("ca_sessions")
        .update({"status": "active"})
        .eq("id", session_id)
        .execute()
    )
    return _safe_data(resp)


def finish_session(session_id: str) -> dict:
    """
    Cambia estado a 'finished'.
    """
    resp = (
        table("ca_sessions")
        .update({"status": "finished"})
        .eq("id", session_id)
        .execute()
    )
    return _safe_data(resp)


def expire_session(session_id: str) -> dict:
    """
    Cambia estado a 'expired'.
    """
    resp = (
        table("ca_sessions")
        .update({"status": "expired"})
        .eq("id", session_id)
        .execute()
    )
    return _safe_data(resp)


# =========================================================
#     EXPIRATION CHECKER (5 DÍAS)
# =========================================================

def check_expired_sessions(operator_id: str) -> t.List[dict]:
    """
    Devuelve sesiones que YA han expirado según expires_at,
    pero aún NO están marcadas como expired.
    """

    allowed = get_operator_allowed_countries(operator_id)

    qb = (
        table("ca_sessions")
        .select("*")
        .eq("status", "active")  # o parked → depende del modelo exacto
        .lt("expires_at", datetime.utcnow().isoformat())
    )
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_data(resp) or []


# =========================================================
#     HIGH-LEVEL OPERATIONS (OPCIONALES)
# =========================================================

def increment_participant_count(session_id: str) -> None:
    """
    (Opcional) Si usas un contador de participantes.
    """
    session = get_session_by_id(session_id)
    if not session:
        return

    participants = session.get("participants_count", 0) + 1

    table("ca_sessions").update(
        {"participants_count": participants}
    ).eq("id", session_id).execute()


def mark_awarded_session(session_id: str, winner_id: str) -> None:
    """
    Marca estado adjudicado en logs o campo interno.
    """
    table("ca_sessions").update(
        {"winner_id": winner_id}
    ).eq("id", session_id).execute()
