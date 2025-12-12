from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event

from backend_core.models.adjudication_models import (
    SessionSnapshot,
    ParticipantSnapshot,
    DeterministicContext,
)

from backend_core.engines.adjudicator_engine_pro import adjudicate


# ==========================================================
# 🔹 CONFIG MOTOR PRO (congelado)
# ==========================================================

ENGINE_VERSION = "2.0.0"
ALGORITHM_ID = "deterministic_sha256_minhash"
NORMALIZATION = "stable_sort_by_participant_id"


# ==========================================================
# 🔹 ERRORES PRO
# ==========================================================

class InvariantViolationError(ValueError):
    """Closed-session invariants or snapshot invariants are not satisfied."""


class ConcurrencyAdjudicationError(RuntimeError):
    """Unexpected concurrency issue when persisting adjudication."""


# ==========================================================
# 🔹 UTILIDADES
# ==========================================================

def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_dt(value) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def _unique_ids(values: List[str]) -> bool:
    return len(values) == len(set(values))


# ==========================================================
# 🔹 CARGA SNAPSHOTS (DB → MODELOS INMUTABLES)
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

    # Debe estar cerrada para adjudicar (aceptamos finished para replay/idempotencia)
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
    # Nota: si tu tabla real fuera ca_session_participants, aquí sería el único cambio.
    resp = (
        table("ca_participants")
        .select("id, user_id, participations, created_at, session_id")
        .eq("session_id", session_id)
        .order("id")  # el motor NO debe depender de esto; solo comodidad de lectura
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


def _load_snapshot_bundle(session_id: str) -> Tuple[SessionSnapshot, List[ParticipantSnapshot]]:
    session_snapshot = _load_session_snapshot(session_id)
    participants_snapshot = _load_participants_snapshot(session_id)

    # Invariantes formales mínimas (antes del motor)
    if len(participants_snapshot) != int(session_snapshot.capacity):
        raise InvariantViolationError(
            f"Aforo incompleto o inconsistente: participants={len(participants_snapshot)} "
            f"capacity={session_snapshot.capacity}."
        )

    ids = [p.participant_id for p in participants_snapshot]
    if not _unique_ids(ids):
        raise InvariantViolationError("Duplicidad de participant_id en el snapshot de participantes.")

    return session_snapshot, participants_snapshot


# ==========================================================
# 🔹 IDEMPOTENCIA (NO DUPLICAR ADJUDICACIONES)
# ==========================================================

def _get_existing_adjudication(session_id: str) -> Optional[Dict[str, Any]]:
    resp = (
        table("ca_adjudications")
        .select("*")
        .eq("session_id", session_id)
        .maybe_single()
        .execute()
    )
    return resp.data if resp else None


# ==========================================================
# 🔹 PERSISTENCIA PRO (DB)
# ==========================================================

def _persist_adjudication_pro(*, session_id: str, result: Any) -> None:
    """
    Guarda la adjudicación PRO en ca_adjudications.
    Inmutable / idempotente por UNIQUE(session_id) en DB.
    """
    payload = {
        "session_id": session_id,
        "awarded_participant_id": result.awarded_participant_id,
        "ranking": result.ranking,
        "seed": result.seed,
        "inputs_hash": result.inputs_hash,
        "proof_hash": result.proof_hash,
        "engine_version": result.engine_version,
        "algorithm_id": result.algorithm_id,
        "created_at": _now_utc_iso(),
    }

    # Importante: asume constraint UNIQUE(session_id) en ca_adjudications.
    table("ca_adjudications").insert(payload).execute()


def _mark_participant_awarded(session_id: str, participant_id: str) -> None:
    """
    Marcado derivado: NO afecta a la inmutabilidad de ca_adjudications.
    Recomendación: además desmarcar el resto para garantizar unicidad.
    """
    # 1) Desmarcar todos los participantes de la sesión (opcional pero recomendado)
    table("ca_participants") \
        .update({"is_awarded": False}) \
        .eq("session_id", session_id) \
        .execute()

    # 2) Marcar adjudicado
    table("ca_participants") \
        .update({"is_awarded": True}) \
        .eq("id", participant_id) \
        .execute()


def _finalize_session(session_id: str, awarded_participant_id: str) -> None:
    """
    Deja la sesión en finished y (si existe columna) guarda awarded_participant_id para lectura rápida.
    Si esa columna no existe, puedes quitarla del update.
    """
    payload = {"status": "finished"}
    # Si tu tabla tiene awarded_participant_id, mantenlo. Si no, elimina esta línea.
    payload["awarded_participant_id"] = awarded_participant_id

    table("ca_sessions") \
        .update(payload) \
        .eq("id", session_id) \
        .execute()


# ==========================================================
# 🔹 SERVICIO PRINCIPAL
# ==========================================================

def adjudicate_session_pro(session_id: str) -> Dict[str, Any]:
    """
    Orquestación PRO:
    - idempotente
    - auditable
    - coherencia semántica (awarded)
    - validación de invariantes
    - robusto ante concurrencia (asumiendo UNIQUE(session_id) en ca_adjudications)
    """

    # 0) Idempotencia rápida
    existing = _get_existing_adjudication(session_id)
    if existing:
        return {
            "session_id": session_id,
            "status": "ALREADY_ADJUDICATED",
            "awarded_participant_id": existing.get("awarded_participant_id"),
            "engine_version": existing.get("engine_version"),
            "algorithm_id": existing.get("algorithm_id"),
        }

    # 1) Snapshots + invariantes
    session_snapshot, participants_snapshot = _load_snapshot_bundle(session_id)

    # 2) Contexto motor (congelado)
    context = DeterministicContext(
        engine_version=ENGINE_VERSION,
        algorithm_id=ALGORITHM_ID,
        normalization=NORMALIZATION,
    )

    # 3) Motor PRO (puro)
    result = adjudicate(
        session=session_snapshot,
        participants=participants_snapshot,
        context=context,
    )

    # 4) Persistencia + marcado awarded + finalize
    #    Sin transacción real (Supabase REST no la garantiza aquí). En su lugar:
    #    - Confiamos en UNIQUE(session_id) para idempotencia fuerte.
    #    - En caso de carrera, leemos la adjudicación existente y devolvemos.
    try:
        _persist_adjudication_pro(session_id=session_id, result=result)
    except Exception:
        # Caso típico: otra ejecución persistió antes (race). Leemos y devolvemos.
        existing_after = _get_existing_adjudication(session_id)
        if existing_after:
            return {
                "session_id": session_id,
                "status": "ALREADY_ADJUDICATED",
                "awarded_participant_id": existing_after.get("awarded_participant_id"),
                "engine_version": existing_after.get("engine_version"),
                "algorithm_id": existing_after.get("algorithm_id"),
            }
        raise ConcurrencyAdjudicationError(
            "Error al persistir adjudicación y no se pudo recuperar el registro existente."
        )

    # Efectos derivados (best-effort; si falla, se puede re-ejecutar idempotente)
    _mark_participant_awarded(session_id=session_id, participant_id=result.awarded_participant_id)
    _finalize_session(session_id=session_id, awarded_participant_id=result.awarded_participant_id)

    # 5) Auditoría
    log_event(
        event_type="session_adjudicated_pro",
        session_id=session_id,
        payload={
            "awarded_participant_id": result.awarded_participant_id,
            "seed": result.seed,
            "inputs_hash": result.inputs_hash,
            "proof_hash": result.proof_hash,
            "engine_version": result.engine_version,
            "algorithm_id": result.algorithm_id,
        },
    )

    return {
        "session_id": session_id,
        "status": "ADJUDICATED",
        "awarded_participant_id": result.awarded_participant_id,
        "engine_version": result.engine_version,
        "algorithm_id": result.algorithm_id,
    }
