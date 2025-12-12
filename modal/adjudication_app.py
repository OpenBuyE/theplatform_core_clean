# modal/adjudication_app.py

import modal
import os
from datetime import datetime, timezone

# -----------------------------
# Modal App
# -----------------------------
app = modal.App("compra-abierta-adjudication-pro")

# -----------------------------
# Imagen Modal (Python limpio)
# -----------------------------
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

# -----------------------------
# Secrets (Supabase)
# -----------------------------
secrets = [
    modal.Secret.from_name("supabase-prod"),
]

# -----------------------------
# Function
# -----------------------------
@app.function(
    image=image,
    secrets=secrets,
    timeout=300,
)
def adjudication_worker(limit: int = 10):
    """
    Worker determinista PRO.
    Ejecuta adjudicaciones pendientes de forma autónoma.
    """

    # ⚠️ IMPORTS DENTRO (Modal best practice)
    from backend_core.services.supabase_client import table
    from backend_core.services.adjudication_service import adjudicate_session
    from backend_core.services.audit_repository import log_event

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
