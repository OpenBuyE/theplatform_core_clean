import hashlib
import datetime
from backend_core.services.supabase_client import table
from backend_core.services.session_repository import (
    get_participants_sorted,
    finish_session,
)
from backend_core.services.audit_repository import log_event


# =====================================================
# 🔹 Obtener semilla usada por una sesión (legacy)
# =====================================================

def get_seed_for_session(session_id: str):
    """
    Devuelve la semilla asociada a una sesión.
    Si no existe campo seed, genera una basada en created_at.
    """
    try:
        result = (
            table("ca_sessions")
            .select("seed, created_at")
            .eq("id", session_id)
            .maybe_single()
            .execute()
        )

        seed = result.get("seed")
        if seed:
            return seed

        created = result.get("created_at", "")
        return hashlib.sha256(created.encode()).hexdigest()

    except Exception:
        return None


# =====================================================
# 🔹 Estado del motor determinista (para Engine Monitor)
# =====================================================

def get_engine_state():
    """
    Snapshot del estado del motor.
    """
    now = datetime.datetime.utcnow().isoformat()
    return {
        "engine": "deterministic_adjudicator",
        "version": "1.0",
        "status": "online",
        "timestamp": now,
    }


# =====================================================
# 🔹 Legacy: get_adjudication_record (solicidad por Engine Monitor)
# =====================================================

def get_adjudication_record(session_id: str):
    """
    Devuelve un registro compatible con versiones antiguas del Engine Monitor.
    No afecta al motor moderno.
    """

    seed = get_seed_for_session(session_id)

    return {
        "session_id": session_id,
        "seed": seed,
        "algorithm": "deterministic_v1",
        "status": "completed_or_pending",
        "details": "legacy compatibility record",
    }


# =====================================================
# 🔹 Motor determinista principal
# =====================================================

def run_adjudication(session_id: str):
    """
    Ejecuta la adjudicación determinista.
    Selección = hash(seed + participant_index) más bajo.
    """

    participants = get_participants_sorted(session_id)
    if not participants:
        raise Exception("No hay participantes en la sesión.")

    seed = get_seed_for_session(session_id)
    if not seed:
        raise Exception("No fue posible obtener la seed.")

    scores = []
    for idx, p in enumerate(participants):
        base = f"{seed}:{idx}:{p['id']}"
        digest = hashlib.sha256(base.encode()).hexdigest()
        scores.append((digest, p))

    scores.sort(key=lambda x: x[0])
    winner = scores[0][1]

    table("ca_participants")\
        .update({"is_awarded": True})\
        .eq("id", winner["id"])\
        .execute()

    finish_session(session_id)

    log_event(
        "session_adjudicated",
        session_id=session_id,
        winner_id=winner["id"],
        seed=seed
    )

    return {
        "winner_participant_id": winner["id"],
        "seed": seed,
        "participants_total": len(participants)
    }
