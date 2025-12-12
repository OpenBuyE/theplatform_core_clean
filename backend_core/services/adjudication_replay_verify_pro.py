from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend_core.services.supabase_client import table
from backend_core.models.adjudication_models import (
    SessionSnapshot,
    ParticipantSnapshot,
    DeterministicContext,
)
from backend_core.engines.adjudicator_engine_pro import adjudicate


# ==========================================================
# 🔹 CONFIG MOTOR PRO (debe coincidir con adjudication_service_pro)
# ==========================================================

ENGINE_VERSION = "2.0.0"
ALGORITHM_ID = "deterministic_sha256_minhash"
NORMALIZATION = "stable_sort_by_participant_id"


# ==========================================================
# 🔹 REPORTES FORMALES (audit-grade)
# ==========================================================

@dataclass(frozen=True)
class ReplayVerifyReport:
    session_id: str
    matches: bool
    reason: str

    db_awarded_participant_id: Optional[str]
    computed_awarded_participant_id: Optional[str]

    db_inputs_hash: Optional[str]
    computed_inputs_hash: Optional[str]

    db_proof_hash: Optional[str]
    computed_proof_hash: Optional[str]

    db_engine_version: Optional[str]
    computed_engine_version: str

    db_algorithm_id: Optional[str]
    computed_algorithm_id: str

    # Opcional (útil en auditoría): diferencias de ranking
    ranking_mismatch_count: int

    verified_at_utc: str


# ==========================================================
# 🔹 UTILIDADES
# ==========================================================

def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_dt(value) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def _normalize_ranking(value: Any) -> List[Any]:
    """
    Normaliza ranking para comparaciones estables.
    Acepta list/dict/jsonb; devuelve lista comparable.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    # Si viniera como dict (poco probable), intentamos una forma estable
    if isinstance(value, dict):
        # orden determinista por clave
        return [{"k": k, "v": value[k]} for k in sorted(value.keys())]
    return [value]


def _ranking_diff_count(db_ranking: Any, computed_ranking: Any) -> int:
    a = _normalize_ranking(db_ranking)
    b = _normalize_ranking(computed_ranking)
    if a == b:
        return 0

    # Conteo aproximado de diferencias por posición (audit-friendly)
    max_len = max(len(a), len(b))
    diff = 0
    for i in range(max_len):
        ai = a[i] if i < len(a) else None
        bi = b[i] if i < len(b) else None
        if ai != bi:
            diff += 1
    return diff


# ==========================================================
# 🔹 CARGA SNAPSHOTS (DB → MODELOS INMUTABLES)
# ==========================================================

class InvariantViolationError(ValueError):
    """Violación de invariantes: sesión no cerrada, aforo incompleto, etc."""


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
        raise InvariantViolationError("Sesión no encontrada.")

    if s.get("status") not in ("closed", "finished"):
        raise InvariantViolationError(
            "La sesión no está en estado cerrado/terminado (closed/finished)."
        )

    if not s.get("closed_at"):
        raise InvariantViolationError("La sesión no tiene closed_at (snapshot no estable).")

    capacity = int(s.get("capacity") or 0)
    if capacity <= 0:
        raise InvariantViolationError("La sesión no tiene capacity válido (>0).")

    return SessionSnapshot(
        session_id=s["id"],
        product_id=s["product_id"],
        session_created_at=_parse_dt(s["created_at"]),
        session_closed_at=_parse_dt(s["closed_at"]),
        capacity=capacity,
        rules_version=s.get("rules_version") or "1.0",
    )


def _load_participants_snapshot(session_id: str) -> List[ParticipantSnapshot]:
    resp = (
        table("ca_participants")
        .select("id, user_id, participations, created_at, session_id")
        .eq("session_id", session_id)
        .order("id")
        .execute()
    )

    rows = resp.data or []
    if not rows:
        raise InvariantViolationError("No hay participantes en la sesión.")

    participants: List[ParticipantSnapshot] = []
    for r in rows:
        participants.append(
            ParticipantSnapshot(
                participant_id=r["id"],
                user_id=r["user_id"],
                participations=int(r.get("participations") or 1),
                joined_at=_parse_dt(r["created_at"]),
            )
        )
    return participants


def _load_snapshot_bundle(session_id: str) -> Tuple[SessionSnapshot, List[ParticipantSnapshot]]:
    session_snapshot = _load_session_snapshot(session_id)
    participants_snapshot = _load_participants_snapshot(session_id)

    if len(participants_snapshot) != int(session_snapshot.capacity):
        raise InvariantViolationError(
            f"Aforo inconsistente: participants={len(participants_snapshot)} "
            f"capacity={session_snapshot.capacity}"
        )

    ids = [p.participant_id for p in participants_snapshot]
    if len(ids) != len(set(ids)):
        raise InvariantViolationError("Duplicidad de participant_id en snapshot de participantes.")

    return session_snapshot, participants_snapshot


# ==========================================================
# 🔹 CARGA ADJUDICACIÓN PERSISTIDA (DB)
# ==========================================================

def _load_db_adjudication(session_id: str) -> Optional[Dict[str, Any]]:
    resp = (
        table("ca_adjudications")
        .select("*")
        .eq("session_id", session_id)
        .maybe_single()
        .execute()
    )
    return resp.data if resp else None


# ==========================================================
# 🔹 API PÚBLICA — REPLAY & VERIFY PRO
# ==========================================================

def replay_verify_session(session_id: str) -> ReplayVerifyReport:
    """
    Recalcula la adjudicación a partir de snapshots inmutables y compara con DB.

    No muta DB. Diseñado para auditoría legal (reproducibilidad demostrable).
    """

    db_row = _load_db_adjudication(session_id)
    if not db_row:
        return ReplayVerifyReport(
            session_id=session_id,
            matches=False,
            reason="NO_ADJUDICATION_IN_DB",
            db_awarded_participant_id=None,
            computed_awarded_participant_id=None,
            db_inputs_hash=None,
            computed_inputs_hash=None,
            db_proof_hash=None,
            computed_proof_hash=None,
            db_engine_version=None,
            computed_engine_version=ENGINE_VERSION,
            db_algorithm_id=None,
            computed_algorithm_id=ALGORITHM_ID,
            ranking_mismatch_count=0,
            verified_at_utc=_now_utc_iso(),
        )

    # DB legacy: winner_participant_id
    db_awarded_participant_id = db_row.get("winner_participant_id")
    db_inputs_hash = db_row.get("inputs_hash")
    db_proof_hash = db_row.get("proof_hash")
    db_engine_version = db_row.get("engine_version")
    db_algorithm_id = db_row.get("algorithm_id")
    db_ranking = db_row.get("ranking")

    # 1) Reconstrucción snapshots
    try:
        session_snapshot, participants_snapshot = _load_snapshot_bundle(session_id)
    except InvariantViolationError as e:
        return ReplayVerifyReport(
            session_id=session_id,
            matches=False,
            reason=f"INVARIANT_VIOLATION: {str(e)}",
            db_awarded_participant_id=db_awarded_participant_id,
            computed_awarded_participant_id=None,
            db_inputs_hash=db_inputs_hash,
            computed_inputs_hash=None,
            db_proof_hash=db_proof_hash,
            computed_proof_hash=None,
            db_engine_version=db_engine_version,
            computed_engine_version=ENGINE_VERSION,
            db_algorithm_id=db_algorithm_id,
            computed_algorithm_id=ALGORITHM_ID,
            ranking_mismatch_count=0,
            verified_at_utc=_now_utc_iso(),
        )

    # 2) Contexto determinista congelado (debe coincidir con el que se usó al persistir)
    ctx = DeterministicContext(
        engine_version=ENGINE_VERSION,
        algorithm_id=ALGORITHM_ID,
        normalization=NORMALIZATION,
    )

    # 3) Replay (motor puro)
    computed = adjudicate(
        session=session_snapshot,
        participants=participants_snapshot,
        context=ctx,
    )

    computed_awarded_participant_id = computed.awarded_participant_id
    computed_inputs_hash = computed.inputs_hash
    computed_proof_hash = computed.proof_hash
    computed_ranking = computed.ranking

    # 4) Comparación
    mismatches: List[str] = []

    if str(db_awarded_participant_id) != str(computed_awarded_participant_id):
        mismatches.append("AWARDED_PARTICIPANT_ID")

    if str(db_inputs_hash) != str(computed_inputs_hash):
        mismatches.append("INPUTS_HASH")

    if str(db_proof_hash) != str(computed_proof_hash):
        mismatches.append("PROOF_HASH")

    if str(db_engine_version) != str(ENGINE_VERSION):
        # No es necesariamente “malo” si soportas múltiples versiones,
        # pero aquí lo marcamos explícito para auditoría.
        mismatches.append("ENGINE_VERSION")

    if str(db_algorithm_id) != str(ALGORITHM_ID):
        mismatches.append("ALGORITHM_ID")

    ranking_diff = _ranking_diff_count(db_ranking, computed_ranking)
    if ranking_diff > 0:
        mismatches.append("RANKING")

    matches = len(mismatches) == 0
    reason = "OK" if matches else "MISMATCH: " + ",".join(mismatches)

    return ReplayVerifyReport(
        session_id=session_id,
        matches=matches,
        reason=reason,
        db_awarded_participant_id=str(db_awarded_participant_id) if db_awarded_participant_id else None,
        computed_awarded_participant_id=str(computed_awarded_participant_id) if computed_awarded_participant_id else None,
        db_inputs_hash=str(db_inputs_hash) if db_inputs_hash else None,
        computed_inputs_hash=str(computed_inputs_hash) if computed_inputs_hash else None,
        db_proof_hash=str(db_proof_hash) if db_proof_hash else None,
        computed_proof_hash=str(computed_proof_hash) if computed_proof_hash else None,
        db_engine_version=str(db_engine_version) if db_engine_version else None,
        computed_engine_version=ENGINE_VERSION,
        db_algorithm_id=str(db_algorithm_id) if db_algorithm_id else None,
        computed_algorithm_id=ALGORITHM_ID,
        ranking_mismatch_count=ranking_diff,
        verified_at_utc=_now_utc_iso(),
    )
