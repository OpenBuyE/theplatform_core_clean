# backend_core/workers/session_adjudication_worker.py

from datetime import datetime, timezone

from backend_core.services.supabase_client import table
from backend_core.services.adjudication_service import adjudicate_session
from backend_core.services.audit_repository import log_event


# ==========================================================
# 🔹 CRITERIO DE SESIÓN LISTA PARA ADJUDICAR
# ==========================================================

def _is_session_ready(session: dict) -> bool:
    """
    Una sesión es adjudicable si:
    - status == 'closed'
    - closed_at NO es null
    - adjudicated_at es null (idempotencia)
    """
    return (
        session.get("status") == "closed"
        and session.get("closed_at") is not None
        and session.get("adjudicated_at") is None
    )


# ==========================================================
# 🔹 WORKER PRINCIPAL
# ==========================================================

def run_session_adjudication_worker(limit: int = 10) -> dict:
    """
    Worker determinista:
    - Busca sesiones cerradas
    - Ejecuta adjudicación PRO
    - Es idempotente
    """

    now = datetime.now(timezone.utc).isoformat()

    resp = (
        table("ca_sessions")
        .select("id, status, closed_at, adjudicated_at")
        .eq("status", "closed")
        .order("closed_at", desc=False)
        .limit(limit)
        .execute()
    )

    sessions = resp.data or []

    processed = []
    skipped = []

    for session in sessions:
        session_id = session["id"]

        if not _is_session_ready(session):
            skipped.append(session_id)
            continue

        try:
            adjudicate_session(session_id)

            # Marcar sesión como adjudicada (idempotencia dura)
            table("ca_sessions") \
                .update({"adjudicated_at": now}) \
                .eq("id", session_id) \
                .execute()

            processed.append(session_id)

        except Exception as e:
            log_event(
                event_type="session_adjudication_failed",
                session_id=session_id,
                payload={"error": str(e)},
            )

    return {
        "timestamp": now,
        "processed": processed,
        "skipped": skipped,
        "processed_count": len(processed),
    }
