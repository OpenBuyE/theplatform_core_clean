# backend_core/services/adjudication_service.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event

from backend_core.models.adjudication_models import (
    SessionSnapshot,
    ParticipantSnapshot,
    DeterministicContext,
)

from backend_core.engines.adjudicator_engine_pro import adjudicate


# ==========================================================
# 🔹 CONSTANTES DEL MOTOR
# ==========================================================

ENGINE_VERSION = "2.0.0"
ALGORITHM_ID = "deterministic_sha256_minhash"
NORMALIZATION = "stable_sort_by_participant_id"


# ==========================================================
# 🔹 CARGA DE SNAPSHOTS DESDE DB
# ==========================================================

def _load_session_snapshot(session_id: str) -> SessionSnapshot:
    """
    Carga el estado cerrado de la sesión.
    La sesión DEBE estar cerrada antes de adjudicar.
    """
    resp = (
        table("ca_sessions")
        .select(
            "id, product_id, created_at, closed_at, capacity, rules_version, status"
        )
        .eq("id", session_id)
        .single()
        .execute()
    )

    data = resp.data
    if not data:
        raise ValueError("Sesión no encontrada.")

    if data.get("status") not in ("closed", "finished"):
        raise ValueError("La sesión no está cerrada para adjudicación.")

    if not data.get("closed_at"):
        raise ValueError("La sesión no tiene closed_at persistido.")

    return SessionSnapshot(
        session_id=data["id"],
        product_id=data["product_id"],
        session_created_at=_parse_dt(data["created_at"]),
        session_closed_at=_parse_dt(data["closed_at"]),
        capacity=data["capacity"],
        rules_version=data.get("rules_version", "1.0"),
    )


def _load_participants_snapshot(session_id: str) -> List[ParticipantSnapshot]:
    """
    Carga la lista cerrada de participantes de la sesión.
    """
    resp = (
        table("ca_participants")
        .select(
            "id, user_id, participations, created_at"
        )
        .eq("session_id", session_id)
        .order("id")
        .execute()
    )

    rows = resp.data or []
    if not rows:
        raise ValueError("No hay participantes en la sesión.")

    snapshots: List[ParticipantSnapshot] = []
    for r in rows:
        snapshots.append(
            ParticipantSnapshot(
                participant_id=r["id"],
                user_id=r["user_id"],
                participations=r.get("participations", 1),
                joined_at=_parse_dt(r["created_at"]),
            )
        )

    return snapshots


# ==========================================================
# 🔹 UTILIDADES
# ==========================================================

def _parse_dt(value) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


# ==========================================================
# 🔹 SERVICIO PRINCIPAL DE ADJUDICACIÓN
# ==========================================================

def adjudicate_session(session_id: str) -> dict:
    """
    Orquesta una adjudicación determinista PRO.

    Flujo:
    1) Carga snapshots (session + participants)
    2) Ejecuta motor PRO
    3) Persiste resultado
    4) Registra auditoría

    Devuelve un dict de resumen (no el resultado completo).
    """

    # 1️⃣ Snapshots
    session_snapshot = _load_session_snapshot(session_id)
    participants_snapshot = _load_participants_snapshot(session_id)

    # 2️⃣ Contexto del motor
    context = DeterministicContext(
        engine_version=ENGINE_VERSION,
        algorithm_id=ALGORITHM_ID,
        normalization=NORMALIZATION,
    )

    # 3️⃣ Ejecución del motor PRO (función pura)
    result = adjudicate(
        session=session_snapshot,
        participants=participants_snapshot,
        context=context,
    )

    # 4️⃣ Persistencia del resultado
    _persist_adjudication(session_id, result)

    # 5️⃣ Auditoría
    log_event(
        event_type="session_adjudicated_pro",
        session_id=session_id,
        payload={
            "winner_participant_id": result.winner_participant_id,
            "seed": result.seed,
            "inputs_hash": result.inputs_hash,
            "proof_hash": result.proof_hash,
            "engine_version": result.engine_version,
            "algorithm_id": result.algorithm_id,
        },
    )

    return {
        "session_id": session_id,
        "winner_participant_id": result.winner_participant_id,
        "engine_version": result.engine_version,
        "algorithm_id": result.algorithm_id,
    }


# ==========================================================
# 🔹 PERSISTENCIA (SEPARADA Y EXPLÍCITA)
# ==========================================================

def _persist_adjudication(session_id: str, result):
    """
    Guarda el resultado de la adjudicación en DB.
    """

    # Marcar ganador
    table("ca_participants") \
        .update({"is_awarded": True}) \
        .eq("id", result.winner_participant_id) \
        .execute()

    # Guardar resultado completo en ca_adjudications
    table("ca_adjudications").insert(
        {
            "session_id": session_id,
            "winner_participant_id": result.winner_participant_id,
            "ranking": result.ranking,
            "seed": result.seed,
            "inputs_hash": result.inputs_hash,
            "proof_hash": result.proof_hash,
            "engine_version": result.engine_version,
            "algorithm_id": result.algorithm_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    ).execute()

    # Cerrar sesión definitivamente
    table("ca_sessions") \
        .update({"status": "finished"}) \
        .eq("id", session_id) \
        .execute()
