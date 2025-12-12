# backend_core/models/adjudication_models.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import hashlib
import json


# ==========================================================
# 🔹 SESSION SNAPSHOT (estado cerrado de la sesión)
# ==========================================================

@dataclass(frozen=True)
class SessionSnapshot:
    """
    Estado inmutable de una sesión en el momento exacto
    en que queda cerrada para adjudicación determinista.
    """

    session_id: str
    product_id: str

    session_created_at: datetime
    session_closed_at: datetime

    capacity: int
    rules_version: str

    def canonical_dict(self) -> dict:
        """
        Representación canónica y ordenada de la sesión
        (base para hashing determinista).
        """
        return {
            "session_id": self.session_id,
            "product_id": self.product_id,
            "session_created_at": self.session_created_at.isoformat(),
            "session_closed_at": self.session_closed_at.isoformat(),
            "capacity": self.capacity,
            "rules_version": self.rules_version,
        }


# ==========================================================
# 🔹 PARTICIPANT SNAPSHOT (participante cerrado)
# ==========================================================

@dataclass(frozen=True)
class ParticipantSnapshot:
    """
    Participante en una sesión cerrada.
    """

    participant_id: str
    user_id: str

    participations: int
    joined_at: datetime

    def canonical_dict(self) -> dict:
        """
        Representación canónica del participante
        (estable y ordenable).
        """
        return {
            "participant_id": self.participant_id,
            "user_id": self.user_id,
            "participations": self.participations,
            "joined_at": self.joined_at.isoformat(),
        }


# ==========================================================
# 🔹 DETERMINISTIC CONTEXT (metadatos del motor)
# ==========================================================

@dataclass(frozen=True)
class DeterministicContext:
    """
    Metadatos del motor determinista.
    No influyen en el resultado matemático,
    pero sí en auditoría y versionado.
    """

    engine_version: str
    algorithm_id: str
    normalization: str

    def canonical_dict(self) -> dict:
        return {
            "engine_version": self.engine_version,
            "algorithm_id": self.algorithm_id,
            "normalization": self.normalization,
        }


# ==========================================================
# 🔹 ADJUDICATION RESULT (resultado formal)
# ==========================================================

@dataclass(frozen=True)
class AdjudicationResult:
    """
    Resultado completo de una adjudicación determinista.
    """

    winner_participant_id: str
    ranking: List[str]

    seed: str
    inputs_hash: str
    proof_hash: str

    engine_version: str
    algorithm_id: str

    def canonical_dict(self) -> dict:
        """
        Representación canónica del resultado.
        """
        return {
            "winner_participant_id": self.winner_participant_id,
            "ranking": self.ranking,
            "seed": self.seed,
            "inputs_hash": self.inputs_hash,
            "proof_hash": self.proof_hash,
            "engine_version": self.engine_version,
            "algorithm_id": self.algorithm_id,
        }


# ==========================================================
# 🔹 CANONICAL HASH HELPERS (USO COMÚN)
# ==========================================================

def canonical_json(data: dict) -> str:
    """
    Serializa un dict de forma estable:
    - claves ordenadas
    - sin espacios
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def sha256_hex(value: str) -> str:
    """
    Devuelve SHA256 hexadecimal de un string.
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
