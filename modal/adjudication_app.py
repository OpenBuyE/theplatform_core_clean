# modal/adjudication_app.py

import modal
from datetime import datetime, timezone
from typing import Dict, Any

# ==========================================================
# Modal App
# ==========================================================
app = modal.App("compra-abierta-adjudication-pro")

# ==========================================================
# Imagen de ejecución
# ==========================================================
image = (
    modal.Image.debian_slim()
    .pip_install(
        "supabase==2.3.5",
        "postgrest",
        "gotrue",
        "storage3",
        "supafunc",
        "bcrypt",
    )
)

# ==========================================================
# Secrets (Supabase Service Role)
# ==========================================================
secrets = [
    modal.Secret.from_name("supabase-prod"),
]

# ==========================================================
# HTTP ENDPOINT
# ==========================================================
@app.function(
    image=image,
    secrets=secrets,
    timeout=300,
)
@modal.web_endpoint(method="POST")
def adjudicate(limit: int = 10) -> Dict[str, Any]:
    """
    Endpoint HTTP para adjudicación determinista PRO.

    Payload opcional:
    {
        "limit": 10
    }
    """

    # ⚠️ Imports internos (Modal best practice)
    from backend_core.services.supabase_client import table
    from backend_core.services.adjudication_service import adjudicate_session
    from backend_core.services.audit_repository import log_event

    now = datetime.now(timezone.utc).isoformat()

    # Buscar sesiones cerradas pendientes de adjudicar
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
    errors = []

    for session in sessions:
        session_id = session["id"]

        # Idempotencia dura
        if session.get("adjudicated_at") is not None:
            skipped.append(session_id)
            continue

        try:
            adjudicate_session(session_id)

            table("ca_sessions") \
                .update({"adjudicated_at": now}) \
                .eq("id", session_id) \
                .execute()

            processed.append(session_id)

        except Exception as e:
            errors.append({
                "session_id": session_id,
                "error": str(e),
            })

            log_event(
                event_type="session_adjudication_failed",
                session_id=session_id,
                payload={"error": str(e)},
            )

    return {
        "engine": "deterministic_adjudicator_pro",
        "timestamp": now,
        "processed_count": len(processed),
        "processed": processed,
        "skipped": skipped,
        "errors": errors,
    }
