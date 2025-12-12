# backend_core/workers/session_closure_worker.py

from datetime import datetime, timezone

from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event


# ==========================================================
# 🔹 HELPERS
# ==========================================================

def _now_utc():
    return datetime.now(timezone.utc).isoformat()


def _session_is_full(session_id: str, capacity: int) -> bool:
    """
    Devuelve True si el número total de participaciones
    alcanza exactamente el aforo de la sesión.
    """
    resp = (
        table("ca_participants")
        .select("participations")
        .eq("session_id", session_id)
        .execute()
    )

    rows = resp.data or []
    total = sum(int(r.get("participations", 0)) for r in rows)

    return total >= capacity


# ==========================================================
# 🔹 WORKER PRINCIPAL
# ==========================================================

def run_session_closure_worker(limit: int = 20) -> dict:
    """
    Cierra automáticamente sesiones que han alcanzado el 100% de aforo.
    """

    now = _now_utc()

    resp = (
        table("ca_sessions")
        .select("id, capacity, status, closed_at")
        .eq("status", "active")
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )

    sessions = resp.data or []

    closed = []
    skipped = []

    for session in sessions:
        session_id = session["id"]
        capacity = int(session.get("capacity") or 0)

        # Seguridad mínima
        if capacity <= 0:
            skipped.append(session_id)
            continue

        # Idempotencia
        if session.get("closed_at") is not None:
            skipped.append(session_id)
            continue

        # ¿Está completa?
        if not _session_is_full(session_id, capacity):
            skipped.append(session_id)
            continue

        # 👉 CIERRE DEFINITIVO
        table("ca_sessions") \
            .update({
                "status": "closed",
                "closed_at": now,
            }) \
            .eq("id", session_id) \
            .execute()

        log_event(
            event_type="session_closed",
            session_id=session_id,
            payload={
                "capacity": capacity,
                "closed_at": now,
            },
        )

        closed.append(session_id)

    return {
        "timestamp": now,
        "closed_sessions": closed,
        "closed_count": len(closed),
        "skipped_count": len(skipped),
    }
