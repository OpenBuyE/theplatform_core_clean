from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

from backend_core.services.supabase_client import table
from backend_core.models.adjudication_models import (
    SessionSnapshot,
    ParticipantSnapshot,
    DeterministicContext,
)
from backend_core.engines.adjudicator_engine_pro import adjudicate


# ==========================================================
# 🔹 CONFIG CONGELADA (debe coincidir con motor/servicios)
# ==========================================================

ENGINE_VERSION = "2.0.0"
ALGORITHM_ID = "deterministic_sha256_minhash"
NORMALIZATION = "stable_sort_by_participant_id"

BUNDLE_SCHEMA_VERSION = "1.0.0"
BUNDLE_ALGORITHM = "sha256(canonical_json)"


# ==========================================================
# 🔹 UTILIDADES
# ==========================================================

def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_dt(value) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json_bytes(obj: Any) -> bytes:
    """
    Canonical JSON estable:
      - sort_keys=True
      - separators sin espacios
      - ensure_ascii=False (mantiene unicode)
    """
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return s.encode("utf-8")


def _bundle_hash(bundle_dict: Dict[str, Any]) -> str:
    return _sha256_hex(_canonical_json_bytes(bundle_dict))


def _participant_min(p: ParticipantSnapshot) -> Dict[str, Any]:
    # Minimal snapshot fields, deterministic & auditable
    return {
        "participant_id": str(p.participant_id),
        "user_id": str(p.user_id),
        "participations": int(getattr(p, "participations", 1)),
        # joined_at no debe influir en el resultado si tu motor no depende de orden de llegada;
        # aún así puede ser útil como evidencia histórica.
        "joined_at": p.joined_at.astimezone(timezone.utc).isoformat() if getattr(p, "joined_at", None) else None,
    }


# ==========================================================
# 🔹 ERRORES
# ==========================================================

class ProofBundleError(RuntimeError):
    pass


class InvariantViolationError(ValueError):
    pass


# ==========================================================
# 🔹 LOAD SNAPSHOTS (DB → MODELOS)
# ==========================================================

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
        raise InvariantViolationError("La sesión no está en estado closed/finished.")

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
# 🔹 API PÚBLICA — GENERACIÓN PROOF BUNDLE
# ==========================================================

@dataclass(frozen=True)
class ProofBundle:
    session_id: str
    bundle: Dict[str, Any]
    bundle_hash: str
    canonical_json: str
    created_at_utc: str


def build_proof_bundle_for_session(
    session_id: str,
    *,
    include_participants: bool = True,
    strict_verify: bool = True,
) -> ProofBundle:
    """
    Genera un Proof Bundle determinista para auditoría/IP.

    - strict_verify=True:
        recalcula el motor y exige coincidencia total con DB (hashes + ranking + awarded).
    - include_participants=True:
        incluye snapshot minimal de participantes (audit-friendly).
    """

    db_row = _load_db_adjudication(session_id)
    if not db_row:
        raise ProofBundleError("No existe adjudicación persistida para esta sesión (ca_adjudications).")

    # DB legacy column
    db_awarded_participant_id = str(db_row.get("winner_participant_id"))
    db_inputs_hash = str(db_row.get("inputs_hash"))
    db_proof_hash = str(db_row.get("proof_hash"))
    db_seed = db_row.get("seed")
    db_ranking = db_row.get("ranking")
    db_engine_version = str(db_row.get("engine_version"))
    db_algorithm_id = str(db_row.get("algorithm_id"))
    db_created_at = str(db_row.get("created_at"))

    # Snapshots
    session_snap = _load_session_snapshot(session_id)
    participant_snaps = _load_participants_snapshot(session_id)

    # Invariantes duras
    if len(participant_snaps) != int(session_snap.capacity):
        raise InvariantViolationError(
            f"Aforo inconsistente: participants={len(participant_snaps)} capacity={session_snap.capacity}"
        )

    ids = [str(p.participant_id) for p in participant_snaps]
    if len(ids) != len(set(ids)):
        raise InvariantViolationError("Duplicidad de participant_id en snapshot de participantes.")

    # Contexto congelado (debe coincidir con DB para IP-grade)
    ctx = DeterministicContext(
        engine_version=ENGINE_VERSION,
        algorithm_id=ALGORITHM_ID,
        normalization=NORMALIZATION,
    )

    computed = adjudicate(
        session=session_snap,
        participants=participant_snaps,
        context=ctx,
    )

    computed_awarded = str(computed.awarded_participant_id)
    computed_inputs_hash = str(computed.inputs_hash)
    computed_proof_hash = str(computed.proof_hash)
    computed_seed = computed.seed
    computed_ranking = computed.ranking

    # Verificación estricta (recomendado para bundle IP)
    if strict_verify:
        mismatches = []
        if computed_awarded != db_awarded_participant_id:
            mismatches.append("awarded_participant_id")
        if computed_inputs_hash != db_inputs_hash:
            mismatches.append("inputs_hash")
        if computed_proof_hash != db_proof_hash:
            mismatches.append("proof_hash")
        if computed_ranking != db_ranking:
            mismatches.append("ranking")
        if db_engine_version != ENGINE_VERSION:
            mismatches.append("engine_version")
        if db_algorithm_id != ALGORITHM_ID:
            mismatches.append("algorithm_id")

        if mismatches:
            raise ProofBundleError("Mismatch DB vs replay: " + ", ".join(mismatches))

    # Snapshot minimal (audit-friendly, sin datos innecesarios)
    participants_min = [_participant_min(p) for p in participant_snaps] if include_participants else None

    bundle_dict: Dict[str, Any] = {
        "bundle_schema_version": BUNDLE_SCHEMA_VERSION,
        "bundle_algorithm": BUNDLE_ALGORITHM,
        "created_at_utc": _now_utc_iso(),
        "session": {
            "session_id": str(session_snap.session_id),
            "product_id": str(session_snap.product_id),
            "capacity": int(session_snap.capacity),
            "rules_version": getattr(session_snap, "rules_version", "1.0"),
            "session_created_at": session_snap.session_created_at.astimezone(timezone.utc).isoformat(),
            "session_closed_at": session_snap.session_closed_at.astimezone(timezone.utc).isoformat(),
        },
        "deterministic_context": {
            "engine_version": ENGINE_VERSION,
            "algorithm_id": ALGORITHM_ID,
            "normalization": NORMALIZATION,
        },
        "db_adjudication": {
            "db_created_at": db_created_at,
            "engine_version": db_engine_version,
            "algorithm_id": db_algorithm_id,
            "awarded_participant_id": db_awarded_participant_id,
            "seed": db_seed,
            "inputs_hash": db_inputs_hash,
            "proof_hash": db_proof_hash,
            "ranking": db_ranking,
        },
        "replay_adjudication": {
            "engine_version": ENGINE_VERSION,
            "algorithm_id": ALGORITHM_ID,
            "awarded_participant_id": computed_awarded,
            "seed": computed_seed,
            "inputs_hash": computed_inputs_hash,
            "proof_hash": computed_proof_hash,
            "ranking": computed_ranking,
        },
        "participants_snapshot_min": participants_min,
        "notes": {
            "terminology": "awarded_participant_id (no lottery, no random, no winner)",
            "db_legacy_column": "winner_participant_id",
        },
    }

    # Hash del bundle canónico (para sellado/registro)
    b_hash = _bundle_hash(bundle_dict)
    canonical = _canonical_json_bytes(bundle_dict).decode("utf-8")

    return ProofBundle(
        session_id=session_id,
        bundle=bundle_dict,
        bundle_hash=b_hash,
        canonical_json=canonical,
        created_at_utc=bundle_dict["created_at_utc"],
    )
