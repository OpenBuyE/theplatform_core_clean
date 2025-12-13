from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from backend_core.services.supabase_client import table
from backend_core.models.adjudication_models import (
    SessionSnapshot,
    ParticipantSnapshot,
    DeterministicContext,
)
from backend_core.engines.adjudicator_engine_pro import (
    adjudicate,
    ExternalEntropySnapshot,
)

# ==========================================================
# Replay & Verify PRO (alineado con drand)
# - Lee adjudicación persistida (ca_adjudications)
# - Recupera snapshots (ca_sessions + ca_participants)
# - Recupera drand/entropy:
#    1) ca_external_entropy (preferente)
#    2) ranking.meta.drand (fallback)
# - Re-ejecuta el motor con external_entropy y compara:
#   awarded_participant_id, inputs_hash, proof_hash, ranking.meta (si aplica)
# ==========================================================

ENGINE_VERSION = "3.0.0"
ALGORITHM_ID = "deterministic_sha256_mod_with_drand_merkle"
NORMALIZATION = "stable_sort_by_entry_hash"


@dataclass(frozen=True)
class ReplayVerifyReport:
    session_id: str
    status: str  # VERIFIED | MISMATCH | NO_STORED_ADJUDICATION
    matches: bool
    reason: Optional[str]

    stored_awarded_participant_id: Optional[str]
    computed_awarded_participant_id: Optional[str]

    stored_inputs_hash: Optional[str]
    computed_inputs_hash: Optional[str]

    stored_proof_hash: Optional[str]
    computed_proof_hash: Optional[str]

    engine_version: str
    algorithm_id: str

    # drand
    entropy_source: Optional[str]  # "ca_external_entropy" | "ranking.meta.drand" | None
    drand_round: Optional[int]
    drand_randomness_hex: Optional[str]
    drand_signature_hex: Optional[str]
    drand_public_key_hex: Optional[str]
    drand_round_time_utc: Optional[str]

    # opcional: payloads resumidos
    notes: Optional[Dict[str, Any]] = None


# -----------------------------
# Utilidades
# -----------------------------

def _parse_dt_iso(value) -> str:
    if value is None:
        return None
    return str(value).replace("+00:00", "Z")


# -----------------------------
# Carga de datos DB
# -----------------------------

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

    if s.get("status") not in ("closed", "finished"):
        raise ValueError("La sesión no está en estado closed/finished (replay requiere snapshot cerrado).")

    if not s.get("closed_at"):
        raise ValueError("La sesión no tiene closed_at (snapshot no estable).")

    capacity = int(s.get("capacity") or 0)
    if capacity <= 0:
        raise ValueError("La sesión no tiene capacity válido (>0).")

    # SessionSnapshot espera datetime; asumimos que tu modelo hace parse,
    # pero aquí lo pasamos como string ISO y dejamos que lo resuelva tu modelo.
    # Si tu SessionSnapshot exige datetime, cambia por tu parse utilitario.
    from datetime import datetime, timezone
    def _parse_dt(v):
        if isinstance(v, datetime):
            return v.astimezone(timezone.utc)
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).astimezone(timezone.utc)

    return SessionSnapshot(
        session_id=str(s["id"]),
        product_id=str(s["product_id"]),
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
        raise ValueError("No hay participantes en la sesión.")

    from datetime import datetime, timezone
    def _parse_dt(v):
        if isinstance(v, datetime):
            return v.astimezone(timezone.utc)
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).astimezone(timezone.utc)

    out: List[ParticipantSnapshot] = []
    for r in rows:
        out.append(
            ParticipantSnapshot(
                participant_id=str(r["id"]),
                user_id=str(r["user_id"]),
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


def _load_entropy_from_table(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Preferente si existe tabla ca_external_entropy y hay fila para esa sesión.
    """
    try:
        resp = (
            table("ca_external_entropy")
            .select("*")
            .eq("session_id", session_id)
            .maybe_single()
            .execute()
        )
        return resp.data if resp else None
    except Exception:
        # Tabla no existe o no accesible: fallback al JSON ranking
        return None


def _extract_entropy_from_ranking_json(ranking: Any) -> Optional[Dict[str, Any]]:
    """
    Fallback legacy/compat: drand embebido en ranking.meta.drand
    """
    if not isinstance(ranking, dict):
        return None
    meta = ranking.get("meta") or {}
    drand = meta.get("drand")
    if not isinstance(drand, dict):
        return None
    return drand


def _to_entropy_snapshot(drand_dict: Dict[str, Any]) -> ExternalEntropySnapshot:
    """
    Normaliza dict -> ExternalEntropySnapshot
    """
    from datetime import datetime, timezone
    def _parse_time(v):
        if not v:
            return None
        s = str(v).replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(s).astimezone(timezone.utc)
        except Exception:
            return None

    return ExternalEntropySnapshot(
        provider=str(drand_dict.get("provider") or "drand"),
        round=int(drand_dict.get("round")),
        randomness_hex=str(drand_dict.get("randomness_hex")),
        signature_hex=drand_dict.get("signature_hex"),
        public_key_hex=drand_dict.get("public_key_hex"),
        round_time_utc=_parse_time(drand_dict.get("round_time_utc")),
    )


# -----------------------------
# Comparación
# -----------------------------

def _compare(stored: Dict[str, Any], computed: Any) -> Tuple[bool, Optional[str]]:
    """
    Comparación mínima (legal-grade):
    - awarded
    - inputs_hash
    - proof_hash
    Opcional: puedes endurecer a ranking completo si lo deseas.
    """
    stored_awarded = str(stored.get("winner_participant_id"))  # legacy DB column
    stored_inputs = str(stored.get("inputs_hash"))
    stored_proof = str(stored.get("proof_hash"))

    computed_awarded = str(computed.awarded_participant_id)
    computed_inputs = str(computed.inputs_hash)
    computed_proof = str(computed.proof_hash)

    mismatches = []
    if stored_awarded != computed_awarded:
        mismatches.append("awarded_participant_id")
    if stored_inputs != computed_inputs:
        mismatches.append("inputs_hash")
    if stored_proof != computed_proof:
        mismatches.append("proof_hash")

    if mismatches:
        return False, "Mismatch DB vs replay: " + ", ".join(mismatches)

    return True, None


# -----------------------------
# API principal
# -----------------------------

def replay_verify_session(session_id: str) -> ReplayVerifyReport:
    stored = _load_stored_adjudication(session_id)
    if not stored:
        return ReplayVerifyReport(
            session_id=session_id,
            status="NO_STORED_ADJUDICATION",
            matches=False,
            reason="No existe adjudicación persistida en ca_adjudications para esta sesión.",
            stored_awarded_participant_id=None,
            computed_awarded_participant_id=None,
            stored_inputs_hash=None,
            computed_inputs_hash=None,
            stored_proof_hash=None,
            computed_proof_hash=None,
            engine_version=ENGINE_VERSION,
            algorithm_id=ALGORITHM_ID,
            entropy_source=None,
            drand_round=None,
            drand_randomness_hex=None,
            drand_signature_hex=None,
            drand_public_key_hex=None,
            drand_round_time_utc=None,
            notes=None,
        )

    # Snapshots
    session_snap = _load_session_snapshot(session_id)
    participants_snap = _load_participants_snapshot(session_id)

    # Context congelado
    context = DeterministicContext(
        engine_version=ENGINE_VERSION,
        algorithm_id=ALGORITHM_ID,
        normalization=NORMALIZATION,
    )

    # Entropía drand: preferente tabla, fallback ranking JSON
    entropy_source = None
    entropy_row = _load_entropy_from_table(session_id)

    drand_dict = None
    if entropy_row:
        entropy_source = "ca_external_entropy"
        drand_dict = {
            "provider": entropy_row.get("provider") or "drand",
            "round": entropy_row.get("round"),
            "randomness_hex": entropy_row.get("randomness_hex"),
            "signature_hex": entropy_row.get("signature_hex"),
            "public_key_hex": entropy_row.get("public_key_hex"),
            "round_time_utc": _parse_dt_iso(entropy_row.get("round_time_utc")),
        }
    else:
        # fallback a ranking JSON
        entropy_source = "ranking.meta.drand"
        drand_dict = _extract_entropy_from_ranking_json(stored.get("ranking"))

    if not drand_dict:
        raise RuntimeError(
            "No se pudo recuperar drand/external entropy para replay. "
            "Crea ca_external_entropy o asegúrate de que ranking.meta.drand exista."
        )

    entropy_snapshot = _to_entropy_snapshot(drand_dict)

    # Re-ejecuta motor
    computed = adjudicate(
        session=session_snap,
        participants=participants_snap,
        context=context,
        external_entropy=entropy_snapshot,
    )

    matches, reason = _compare(stored, computed)

    return ReplayVerifyReport(
        session_id=session_id,
        status="VERIFIED" if matches else "MISMATCH",
        matches=matches,
        reason=reason,
        stored_awarded_participant_id=str(stored.get("winner_participant_id")),
        computed_awarded_participant_id=str(computed.awarded_participant_id),
        stored_inputs_hash=str(stored.get("inputs_hash")),
        computed_inputs_hash=str(computed.inputs_hash),
        stored_proof_hash=str(stored.get("proof_hash")),
        computed_proof_hash=str(computed.proof_hash),
        engine_version=ENGINE_VERSION,
        algorithm_id=ALGORITHM_ID,
        entropy_source=entropy_source,
        drand_round=int(drand_dict.get("round")) if drand_dict.get("round") is not None else None,
        drand_randomness_hex=drand_dict.get("randomness_hex"),
        drand_signature_hex=drand_dict.get("signature_hex"),
        drand_public_key_hex=drand_dict.get("public_key_hex"),
        drand_round_time_utc=drand_dict.get("round_time_utc"),
        notes={
            "db_legacy_column": "winner_participant_id",
            "terminology": "awarded_participant_id (core), winner_participant_id (DB legacy)",
        },
    )
