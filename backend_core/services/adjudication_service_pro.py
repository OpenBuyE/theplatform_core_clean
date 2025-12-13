from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

import os

from backend_core.services.supabase_client import table, supabase
from backend_core.services.audit_repository import log_event

from backend_core.models.adjudication_models import (
    SessionSnapshot,
    ParticipantSnapshot,
    DeterministicContext,
)

from backend_core.engines.adjudicator_engine_pro import (
    adjudicate,
    ExternalEntropySnapshot,
)

from backend_core.services.drand_provider import (
    DrandConfig,
    HttpDrandProvider,
)

# ==========================================================
# 🔹 CONFIG MOTOR PRO (congelado)
# ==========================================================

ENGINE_VERSION = "3.0.0"
ALGORITHM_ID = "deterministic_sha256_mod_with_drand_merkle"
NORMALIZATION = "stable_sort_by_entry_hash"

# Política drand: first round with time >= closed_at + Δ
DRAND_BASE_URL = os.getenv("DRAND_BASE_URL", "https://api.drand.sh")
DRAND_NOT_BEFORE_DELAY_SECONDS = int(os.getenv("DRAND_NOT_BEFORE_DELAY_SECONDS", "30"))

# En modo IP-grade, drand es obligatorio
REQUIRE_DRAND = os.getenv("REQUIRE_DRAND", "true").lower() in ("1", "true", "yes", "on")

# ==========================================================
# 🔹 UTILIDADES
# ==========================================================

def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_dt(value) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


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
        raise ValueError("Sesión no encontrada.")

    # La sesión debe estar cerrada para adjudicar
    if s.get("status") not in ("closed", "finished"):
        raise ValueError("La sesión no está en estado cerrado/terminado (closed/finished).")

    if not s.get("closed_at"):
        raise ValueError("La sesión no tiene closed_at (snapshot no estable).")

    capacity = int(s.get("capacity") or 0)
    if capacity <= 0:
        raise ValueError("La sesión no tiene capacity válido (>0).")

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
# 🔹 DRAND (ENTROPÍA PÚBLICA VERIFICABLE)
# ==========================================================

def _get_drand_entropy(session_closed_at_utc: datetime) -> Optional[ExternalEntropySnapshot]:
    """
    Obtiene el primer round drand cuyo timestamp >= closed_at + Δ.
    La verificación de firma/chain (si la añades) debe vivir en el provider o en un verifier externo.
    """
    cfg = DrandConfig(base_url=DRAND_BASE_URL, timeout_seconds=10)
    provider = HttpDrandProvider(cfg)

    not_before = session_closed_at_utc.astimezone(timezone.utc) + timedelta(seconds=DRAND_NOT_BEFORE_DELAY_SECONDS)

    try:
        return provider.get_round_after(not_before_utc=not_before)
    except Exception:
        if REQUIRE_DRAND:
            raise
        return None


# ==========================================================
# 🔹 PERSISTENCIA PRO (DB) — Atomicidad preferente via RPC
# ==========================================================

def _finalize_via_rpc(
    *,
    session_id: str,
    winner_participant_id: str,  # columna legacy en DB
    ranking: Any,
    seed: str,
    inputs_hash: str,
    proof_hash: str,
    engine_version: str,
    algorithm_id: str,
) -> bool:
    """
    Intenta ejecutar la función Postgres 'ca_finalize_adjudication_pro' (si existe)
    para insertar adjudicación + marcar awarded + finalizar sesión en transacción.
    Devuelve True si la RPC se ejecutó; False si no.
    """
    try:
        # Convención: pasar nombres = columnas (muy común en RPCs Supabase).
        payload = {
            "session_id": session_id,
            "winner_participant_id": winner_participant_id,
            "ranking": ranking,
            "seed": seed,
            "inputs_hash": inputs_hash,
            "proof_hash": proof_hash,
            "engine_version": engine_version,
            "algorithm_id": algorithm_id,
        }
        supabase.rpc("ca_finalize_adjudication_pro", payload).execute()
        return True
    except Exception:
        # Fallback silencioso: usamos persistencia manual si la RPC no encaja con firma/nombres
        return False


def _persist_manual(
    *,
    session_id: str,
    winner_participant_id: str,
    ranking: Any,
    seed: str,
    inputs_hash: str,
    proof_hash: str,
    engine_version: str,
    algorithm_id: str,
) -> None:
    """
    Persistencia manual (fallback):
    - inserta ca_adjudications
    - marca participante (is_awarded)
    - finaliza sesión (finished)
    Nota: no es tan fuerte como RPC transaccional, pero no rompe el sistema.
    """
    table("ca_adjudications").insert(
        {
            "session_id": session_id,
            "winner_participant_id": winner_participant_id,
            "ranking": ranking,
            "seed": seed,
            "inputs_hash": inputs_hash,
            "proof_hash": proof_hash,
            "engine_version": engine_version,
            "algorithm_id": algorithm_id,
            "created_at": _now_utc_iso(),
        }
    ).execute()

    table("ca_participants").update({"is_awarded": True}).eq("id", winner_participant_id).execute()
    table("ca_sessions").update({"status": "finished"}).eq("id", session_id).execute()


# ==========================================================
# 🔹 SERVICIO PRINCIPAL
# ==========================================================

def adjudicate_session_pro(session_id: str) -> Dict[str, Any]:
    """
    Orquestación PRO:
    - Idempotente
    - Audit-grade
    - Alineado con documentación IP: drand + manifest_commit + mod N
    - Terminología externa: awarded
      (DB legacy: winner_participant_id)
    """

    # 0) Idempotencia
    existing = _get_existing_adjudication(session_id)
    if existing:
        return {
            "session_id": session_id,
            "status": "ALREADY_ADJUDICATED",
            "awarded_participant_id": existing.get("winner_participant_id"),
            "engine_version": existing.get("engine_version"),
            "algorithm_id": existing.get("algorithm_id"),
        }

    # 1) Snapshots
    session_snapshot = _load_session_snapshot(session_id)
    participants_snapshot = _load_participants_snapshot(session_id)

    # 2) Contexto motor (congelado)
    context = DeterministicContext(
        engine_version=ENGINE_VERSION,
        algorithm_id=ALGORITHM_ID,
        normalization=NORMALIZATION,
    )

    # 3) Drand entropy (obligatorio en modo IP-grade)
    entropy = _get_drand_entropy(session_snapshot.session_closed_at)
    if REQUIRE_DRAND and entropy is None:
        raise RuntimeError("DRAND requerido pero no disponible.")

    # 4) Motor PRO (puro)
    result = adjudicate(
        session=session_snapshot,
        participants=participants_snapshot,
        context=context,
        external_entropy=entropy,  # <-- alineación IP
    )

    # 5) Persistencia
    # DB schema legacy: winner_participant_id
    winner_participant_id = str(result.awarded_participant_id)

    did_rpc = _finalize_via_rpc(
        session_id=session_id,
        winner_participant_id=winner_participant_id,
        ranking=result.ranking,
        seed=result.seed,
        inputs_hash=result.inputs_hash,
        proof_hash=result.proof_hash,
        engine_version=result.engine_version,
        algorithm_id=result.algorithm_id,
    )

    if not did_rpc:
        _persist_manual(
            session_id=session_id,
            winner_participant_id=winner_participant_id,
            ranking=result.ranking,
            seed=result.seed,
            inputs_hash=result.inputs_hash,
            proof_hash=result.proof_hash,
            engine_version=result.engine_version,
            algorithm_id=result.algorithm_id,
        )

    # 6) Auditoría (terminología awarded)
    # drand queda embebido en ranking.meta.drand; lo reflejamos también en log_event.
    drand_meta = None
    try:
        drand_meta = (result.ranking or {}).get("meta", {}).get("drand")
    except Exception:
        drand_meta = None

    log_event(
        event_type="session_adjudicated_pro",
        session_id=session_id,
        payload={
            "awarded_participant_id": winner_participant_id,
            "seed": result.seed,
            "inputs_hash": result.inputs_hash,
            "proof_hash": result.proof_hash,
            "engine_version": result.engine_version,
            "algorithm_id": result.algorithm_id,
            "drand": drand_meta,
        },
    )

    return {
        "session_id": session_id,
        "status": "ADJUDICATED",
        "awarded_participant_id": winner_participant_id,
        "engine_version": result.engine_version,
        "algorithm_id": result.algorithm_id,
        "drand": drand_meta,
        "persistence_mode": "RPC" if did_rpc else "MANUAL",
    }
