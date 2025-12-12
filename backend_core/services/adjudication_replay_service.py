# backend_core/services/adjudication_replay_service.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from backend_core.services.supabase_client import table
from backend_core.models.adjudication_models import (
    SessionSnapshot,
    ParticipantSnapshot,
    DeterministicContext,
)
from backend_core.engines.adjudicator_engine_pro import adjudicate


ENGINE_VERSION = "2.0.0"
ALGORITHM_ID = "deterministic_sha256_minhash"
NORMALIZATION = "stable_sort_by_participant_id"


def _parse_dt(value) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def _load_session_snapshot(session_id: str) -> SessionSnapshot:
    resp = (
        table("ca_sessions")
        .select("id, product_id, created_at, closed_at, capacity, rules_version, status")
        .eq("id", session_id)
        .single()
        .execute()
    )
    s = resp.data
    if not s:
        raise ValueError("Sesión no encontrada.")

    if not s.get("closed_at"):
        raise ValueError("La sesión no tiene closed_at (no es replayable/auditable).")

    return SessionSnapshot(
        session_id=s["id"],
        product_id=s["product_id"],
        session_created_at=_parse_dt(s["created_at"]),
        session_closed_at=_parse_dt(s["closed_at"]),
        capacity=int(s.get("capacity") or 0),
        rules_version=s.get("rules_version") or "1.0",
    )


def _load_participants_snapshot(session_id: str) -> List[ParticipantSnapshot]:
    # Nota: si tu tabla real se llama distinto (p.ej. ca_session_participants),
    # aquí es el único sitio que habría que adaptar.
    resp = (
        table("ca_participants")
        .select("id, user_id, participations, created_at")
        .eq("session_id", session_id)
        .order("id")
        .execute()
    )
    rows = resp.data or []
    if not rows:
        raise ValueError("No hay participantes para replay.")

    out: List[ParticipantSnapshot] = []
    for r in rows:
        out.append(
            ParticipantSnapshot(
                participant_id=r["id"],
                user_id=r["user_id"],
                participations=int(r.get("participations") or 1),
                joined_at=_parse_dt(r["created_at"]),
            )
        )
    return out


def _load_stored_adjudication(session_id: str) -> Optional[Dict[str, Any]]:
    resp = (
        table("ca_adjudications")
        .select("*")
        .eq("session_id", session_id)
        .maybe_single()
        .execute()
    )
    return resp.data if resp else None


def replay_and_verify(session_id: str) -> Dict[str, Any]:
    """
    Recalcula la adjudicación PRO desde snapshots y verifica contra lo guardado en DB.
    Devuelve un dict apto para mostrar en UI/auditoría.
    """
    session = _load_session_snapshot(session_id)
    participants = _load_participants_snapshot(session_id)

    context = DeterministicContext(
        engine_version=ENGINE_VERSION,
        algorithm_id=ALGORITHM_ID,
        normalization=NORMALIZATION,
    )

    recalculated = adjudicate(session=session, participants=participants, context=context)
    stored = _load_stored_adjudication(session_id)

    if not stored:
        return {
            "session_id": session_id,
            "status": "NO_STORED_ADJUDICATION",
            "recalculated": {
                "winner_participant_id": recalculated.winner_participant_id,
                "seed": recalculated.seed,
                "inputs_hash": recalculated.inputs_hash,
                "proof_hash": recalculated.proof_hash,
                "engine_version": recalculated.engine_version,
                "algorithm_id": recalculated.algorithm_id,
            },
        }

    winner_ok = str(stored.get("winner_participant_id")) == str(recalculated.winner_participant_id)
    proof_ok = str(stored.get("proof_hash")) == str(recalculated.proof_hash)
    inputs_ok = str(stored.get("inputs_hash")) == str(recalculated.inputs_hash)

    return {
        "session_id": session_id,
        "status": "VERIFIED" if (winner_ok and proof_ok and inputs_ok) else "MISMATCH",
        "checks": {
            "winner_ok": winner_ok,
            "proof_ok": proof_ok,
            "inputs_ok": inputs_ok,
        },
        "stored": {
            "winner_participant_id": stored.get("winner_participant_id"),
            "seed": stored.get("seed"),
            "inputs_hash": stored.get("inputs_hash"),
            "proof_hash": stored.get("proof_hash"),
            "engine_version": stored.get("engine_version"),
            "algorithm_id": stored.get("algorithm_id"),
        },
        "recalculated": {
            "winner_participant_id": recalculated.winner_participant_id,
            "seed": recalculated.seed,
            "inputs_hash": recalculated.inputs_hash,
            "proof_hash": recalculated.proof_hash,
            "engine_version": recalculated.engine_version,
            "algorithm_id": recalculated.algorithm_id,
        },
    }
