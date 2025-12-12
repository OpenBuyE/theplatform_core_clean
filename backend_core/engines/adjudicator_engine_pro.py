# backend_core/engines/adjudicator_engine_pro.py

from __future__ import annotations

from typing import List
from datetime import datetime

from backend_core.models.adjudication_models import (
    SessionSnapshot,
    ParticipantSnapshot,
    DeterministicContext,
    AdjudicationResult,
    canonical_json,
    sha256_hex,
)


# ==========================================================
# 🔹 VALIDACIONES DE ENTRADA
# ==========================================================

def _validate_inputs(
    session: SessionSnapshot,
    participants: List[ParticipantSnapshot],
):
    if not participants:
        raise ValueError("No hay participantes para adjudicar.")

    if session.capacity <= 0:
        raise ValueError("La capacidad de la sesión debe ser positiva.")

    if len(participants) > session.capacity:
        raise ValueError("Participantes exceden la capacidad de la sesión.")

    ids = [p.participant_id for p in participants]
    if len(ids) != len(set(ids)):
        raise ValueError("Hay participant_id duplicados.")

    for p in participants:
        if p.participations <= 0:
            raise ValueError("Las participaciones deben ser >= 1.")


# ==========================================================
# 🔹 CONSTRUCCIÓN DE LA SEED DETERMINISTA
# ==========================================================

def _build_seed(
    session: SessionSnapshot,
    participants: List[ParticipantSnapshot],
) -> str:
    """
    Construye la seed determinista a partir del estado cerrado.
    """

    sorted_participants = sorted(
        participants,
        key=lambda p: p.participant_id,
    )

    seed_material = {
        "session": session.canonical_dict(),
        "participants": [
            p.canonical_dict() for p in sorted_participants
        ],
        "participants_total": len(participants),
    }

    return sha256_hex(canonical_json(seed_material))


# ==========================================================
# 🔹 CÁLCULO DE SCORES DETERMINISTAS
# ==========================================================

def _score_participant(
    seed: str,
    participant: ParticipantSnapshot,
) -> str:
    """
    Calcula el score determinista de un participante.
    """

    material = {
        "seed": seed,
        "participant_id": participant.participant_id,
        "user_id": participant.user_id,
        "participations": participant.participations,
        "joined_at": participant.joined_at.isoformat(),
    }

    return sha256_hex(canonical_json(material))


# ==========================================================
# 🔹 MOTOR PRINCIPAL (FUNCIÓN PURA)
# ==========================================================

def adjudicate(
    *,
    session: SessionSnapshot,
    participants: List[ParticipantSnapshot],
    context: DeterministicContext,
) -> AdjudicationResult:
    """
    Ejecuta la adjudicación determinista PRO.

    - Función pura
    - Reproducible
    - Auditable
    """

    # 1️⃣ Validaciones
    _validate_inputs(session, participants)

    # 2️⃣ Seed determinista
    seed = _build_seed(session, participants)

    # 3️⃣ Scores por participante
    scored = []
    for p in participants:
        score = _score_participant(seed, p)
        scored.append((score, p.participant_id))

    # 4️⃣ Ordenación determinista
    scored.sort(key=lambda x: x[0])

    ranking = [pid for _, pid in scored]
    winner_participant_id = ranking[0]

    # 5️⃣ Hash de inputs (prueba de replay)
    inputs_material = {
        "session": session.canonical_dict(),
        "participants": [p.canonical_dict() for p in participants],
        "context": context.canonical_dict(),
    }
    inputs_hash = sha256_hex(canonical_json(inputs_material))

    # 6️⃣ Proof hash (prueba de resultado)
    proof_material = {
        "seed": seed,
        "ranking": ranking,
    }
    proof_hash = sha256_hex(canonical_json(proof_material))

    # 7️⃣ Resultado final
    return AdjudicationResult(
        winner_participant_id=winner_participant_id,
        ranking=ranking,
        seed=seed,
        inputs_hash=inputs_hash,
        proof_hash=proof_hash,
        engine_version=context.engine_version,
        algorithm_id=context.algorithm_id,
    )
