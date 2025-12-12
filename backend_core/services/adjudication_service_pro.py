from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from backend_core.services.supabase_client import table

# ✅ Intentamos importar el cliente supabase para usar rpc()
# Si tu supabase_client.py no expone 'supabase', ajusta este import.
try:
    from backend_core.services.supabase_client import supabase  # type: ignore
except Exception:  # pragma: no cover
    supabase = None  # fallback controlado

from backend_core.services.audit_repository import log_event

from backend_core.models.adjudication_models import (
    SessionSnapshot,
    ParticipantSnapshot,
    DeterministicContext,
)

from backend_core.engines.adjudicator_engine_pro import adjudicate


# ==========================================================
# 🔹 CONFIGURACIÓN CONGELADA — MOTOR DETERMINISTA PRO
# ==========================================================

ENGINE_VERSION = "2.0.0"
ALGORITHM_ID = "deterministic_sha256_minhash"
NORMALIZATION = "stable_sort_by_participant_id"

RPC_FINALIZE = "ca_finalize_adjudication_pro"


# ==========================================================
# 🔹 ERRORES DOMINIO
# ==========================================================

class InvariantViolationError(ValueError):
    """Violación de invariantes deterministas (sesión, snapshots, aforo, etc.)."""


class ConcurrencyAdjudicationError(RuntimeError):
    """Error inesperado de concurrencia durante la adjudicación."""


class RpcNotAvailableError(RuntimeError):
    """El cliente Supabase no expone rpc(); requiere wrapper en supabase_client.py."""


# ==========================================================
# 🔹 UTILIDADES
# ==========================================================

def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_dt(value) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def _unique(values: List[str]) -> bool:
    return len(values) == len(set(values))


# ==========================================================
# 🔹 SNAPSHOTS INMUTABLES (DB → MODELOS)
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
        .order("id")  # solo lectura; el motor no depende del orden
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


def _load_snapshot_bundle(
    session_id: str,
) -> Tuple[SessionSnapshot, List[ParticipantSnapshot]]:
    session_snapshot = _load_session_snapshot(session_id)
    participants_snapshot = _load_participants_snapshot(session_id)

    # Invariantes deterministas duras
    if len(participants_snapshot) != int(session_snapshot.capacity):
        raise InvariantViolationError(
            f"Aforo inconsistente: participants={len(participants_snapshot)} "
            f"capacity={session_snapshot.capacity}"
        )

    ids = [p.participant_id for p in participants_snapshot]
    if not _unique(ids):
        raise InvariantViolationError(
            "Duplicidad de participant_id en snapshot de participantes."
        )

    return session_snapshot, participants_snapshot


# ==========================================================
# 🔹 IDEMPOTENCIA (LECTURA DB)
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
# 🔹 RPC FINALIZE (ATÓMICO)
# ==========================================================

def _rpc_finalize_adjudication(
    *,
    session_id: str,
    awarded_participant_id: str,
    result: Any,
) -> Dict[str, Any]:
    """
    Llama a la RPC transaccional en Postgres:
      public.ca_finalize_adjudication_pro(...)
    Mantiene semántica awarded; DB legacy usa winner_participant_id internamente.
    """
    if supabase is None or not hasattr(supabase, "rpc"):
        raise RpcNotAvailableError(
            "Supabase client no disponible o no expone rpc(). "
            "Expón `supabase` en supabase_client.py o añade wrapper rpc()."
        )

    payload = {
        "p_session_id": session_id,
        "p_awarded_participant_id": awarded_participant_id,
        "p_ranking": result.ranking,
        "p_seed": result.seed,
        "p_inputs_hash": result.inputs_hash,
        "p_proof_hash": result.proof_hash,
        "p_engine_version": result.engine_version,
        "p_algorithm_id": result.algorithm_id,
    }

    resp = supabase.rpc(RPC_FINALIZE, payload).execute()
    data = resp.data

    # PostgREST suele devolver lista con 1 fila (returns table)
    if isinstance(data, list) and data:
        return data[0]
    if isinstance(data, dict) and data:
        return data

    # Si no hay data, levantamos con contexto
    raise RuntimeError(f"RPC {RPC_FINALIZE} devolvió respuesta vacía: {data!r}")


# ==========================================================
# 🔹 SERVICIO PÚBLICO — ORQUESTACIÓN DETERMINISTA PRO (ATÓMICO)
# ==========================================================

def adjudicate_session_pro(session_id: str) -> Dict[str, Any]:
    """
    Servicio determinista PRO (ATÓMICO via RPC):

    - Idempotente (UNIQUE session_id en DB)
    - Reproducible
    - Auditable
    - Semántica awarded (no lottery, no winner)
    - Persistencia + marcado + finalización en una sola transacción SQL
    """

    # 0) Idempotencia rápida (fast path)
    existing = _get_existing_adjudication(session_id)
    if existing:
        return {
            "session_id": session_id,
            "status": "ALREADY_ADJUDICATED",
            # DB legacy column:
            "awarded_participant_id": existing.get("winner_participant_id"),
            "engine_version": existing.get("engine_version"),
            "algorithm_id": existing.get("algorithm_id"),
        }

    # 1) Snapshots inmutables + invariantes
    session_snapshot, participants_snapshot = _load_snapshot_bundle(session_id)

    # 2) Contexto determinista congelado
    context = DeterministicContext(
        engine_version=ENGINE_VERSION,
        algorithm_id=ALGORITHM_ID,
        normalization=NORMALIZATION,
    )

    # 3) Motor determinista puro
    result = adjudicate(
        session=session_snapshot,
        participants=participants_snapshot,
        context=context,
    )

    awarded_participant_id = result.awarded_participant_id

    # 4) Finalización atómica (DB transaction)
    try:
        rpc_out = _rpc_finalize_adjudication(
            session_id=session_id,
            awarded_participant_id=awarded_participant_id,
            result=result,
        )
    except RpcNotAvailableError:
        # Fallback ultra conservador: no hacemos updates sueltos aquí.
        # Preferimos fallar explícitamente para no volver a estados intermedios.
        raise
    except Exception:
        # Si por concurrencia ya existe, devolvemos lo persistido
        existing_after = _get_existing_adjudication(session_id)
        if existing_after:
            return {
                "session_id": session_id,
                "status": "ALREADY_ADJUDICATED",
                "awarded_participant_id": existing_after.get("winner_participant_id"),
                "engine_version": existing_after.get("engine_version"),
                "algorithm_id": existing_after.get("algorithm_id"),
            }
        raise ConcurrencyAdjudicationError(
            "Fallo en finalización atómica y no se pudo recuperar la adjudicación existente."
        )

    # 5) Auditoría (fuera de la transacción; evidencia criptográfica ya persistida)
    log_event(
        event_type="session_adjudicated_pro",
        session_id=session_id,
        payload={
            "awarded_participant_id": awarded_participant_id,
            "seed": result.seed,
            "inputs_hash": result.inputs_hash,
            "proof_hash": result.proof_hash,
            "engine_version": result.engine_version,
            "algorithm_id": result.algorithm_id,
            "rpc_status": rpc_out.get("status") if isinstance(rpc_out, dict) else None,
        },
    )

    # 6) Respuesta estable (semántica awarded)
    return {
        "session_id": session_id,
        "status": rpc_out.get("status", "ADJUDICATED") if isinstance(rpc_out, dict) else "ADJUDICATED",
        "awarded_participant_id": (
            rpc_out.get("awarded_participant_id") if isinstance(rpc_out, dict) else awarded_participant_id
        ),
        "engine_version": result.engine_version,
        "algorithm_id": result.algorithm_id,
    }
