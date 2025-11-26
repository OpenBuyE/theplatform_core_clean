# backend_core/services/session_repository.py

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from backend_core.services.supabase_client import table


# ============================
# Helpers
# ============================

def _now_utc() -> datetime:
    return datetime.utcnow()


def _five_days_from_now() -> datetime:
    return _now_utc() + timedelta(days=5)


def _rows(q) -> list[dict]:
    res = q.execute()
    return res or []


# ============================
# CREACIÓN / MUTACIONES
# ============================

def create_parked_session(product_id: str, capacity: int, series_id: Optional[str] = None) -> str:
    """
    Crea una sesión en estado 'parked'.
    """
    payload = {
        "product_id": product_id,
        "aforo": capacity,
        "status": "parked",
        "created_at": _now_utc().isoformat(),
        "expires_at": _five_days_from_now().isoformat(),
    }
    if series_id:
        payload["series_id"] = series_id

    rows = table("ca_sessions").insert(payload).execute()
    if not rows:
        raise RuntimeError("No se pudo crear la sesión parked.")
    return rows[0]["id"]


def activate_session(session_id: str):
    """
    Marca una sesión como 'active' y fija activated_at.
    """
    table("ca_sessions").update(
        {
            "status": "active",
            "activated_at": _now_utc().isoformat(),
        }
    ).eq("id", session_id).execute()


def finish_session(session_id: str):
    """
    Marca una sesión como 'finished'.
    """
    table("ca_sessions").update(
        {
            "status": "finished",
            "finished_at": _now_utc().isoformat(),
        }
    ).eq("id", session_id).execute()


def expire_session(session_id: str):
    """
    Marca una sesión como 'expired'.
    """
    table("ca_sessions").update(
        {
            "status": "expired",
            "expires_at": _now_utc().isoformat(),
        }
    ).eq("id", session_id).execute()


# ============================
# LECTURAS POR ESTADO
# ============================

def get_parked_sessions(operator_id: Optional[str] = None) -> List[Dict[str, Any]]:
    q = table("ca_sessions").select("*").eq("status", "parked").order("created_at", desc=True)
    return _rows(q)


def get_active_sessions(operator_id: Optional[str] = None) -> List[Dict[str, Any]]:
    q = table("ca_sessions").select("*").eq("status", "active").order("created_at", desc=True)
    return _rows(q)


def get_finished_sessions(operator_id: Optional[str] = None) -> List[Dict[str, Any]]:
    q = table("ca_sessions").select("*").eq("status", "finished").order("finished_at", desc=True)
    return _rows(q)


def get_expired_sessions(operator_id: Optional[str] = None) -> List[Dict[str, Any]]:
    q = table("ca_sessions").select("*").eq("status", "expired").order("expires_at", desc=True)
    return _rows(q)


def get_scheduled_sessions(operator_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Para scheduled_sessions.py – sesiones planificadas futuras.
    """
    q = table("ca_sessions").select("*").eq("status", "scheduled").order("created_at", desc=True)
    return _rows(q)


def get_standby_sessions(operator_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Para standby_sessions.py – sesiones en standby/manual.
    """
    q = table("ca_sessions").select("*").eq("status", "standby").order("created_at", desc=True)
    return _rows(q)


def get_all_sessions(operator_id: Optional[str] = None) -> List[Dict[str, Any]]:
    q = table("ca_sessions").select("*").order("created_at", desc=True)
    return _rows(q)


# ============================
# SERIES / CHAINS
# ============================

def get_session_series(operator_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Devuelve las series (ca_session_series). Si no existe la tabla,
    puedes cambiar esto a un DISTINCT series_id sobre ca_sessions.
    """
    try:
        q = table("ca_session_series").select("*").order("created_at", desc=True)
        return _rows(q)
    except Exception:
        # Fallback: series distintas en ca_sessions
        q = table("ca_sessions").select("series_id").neq("series_id", None)
        rows = _rows(q)
        series_ids = sorted({r["series_id"] for r in rows if r.get("series_id")})
        return [{"id": sid} for sid in series_ids]


def get_sessions_by_series(series_id: str, operator_id: Optional[str] = None) -> List[Dict[str, Any]]:
    q = (
        table("ca_sessions")
        .select("*")
        .eq("series_id", series_id)
        .order("created_at", desc=True)
    )
    return _rows(q)
