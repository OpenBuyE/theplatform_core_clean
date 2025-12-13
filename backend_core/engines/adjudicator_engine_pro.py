from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend_core.models.adjudication_models import (
    SessionSnapshot,
    ParticipantSnapshot,
    DeterministicContext,
)

# ==========================================================
# 🔹 MOTOR DETERMINISTA PRO (alineado con anexos IP)
# - manifest_commit = SHA256(manifest_json_canónico)
# - participants_merkle_root (sobre entradas/participaciones)
# - seed = H(session_id || merkle_root || N || drand_round || drand_randomness || manifest_commit)
# - idx = int(seed,16) mod N
# - awarded = entry[idx] -> participant
# - proof_hash = H(proof_bundle_canónico)
# ==========================================================

ENGINE_VERSION_DEFAULT = "3.0.0"
ALGORITHM_ID_DEFAULT = "deterministic_sha256_mod_with_drand_merkle"


# ==========================================================
# 🔹 MODELOS AUXILIARES (no rompen compatibilidad externa)
# ==========================================================

@dataclass(frozen=True)
class ExternalEntropySnapshot:
    """
    Entropía pública verificable (drand) usada como input del cálculo.
    La verificación criptográfica de drand la realiza el módulo drand (fuera del motor).
    El motor asume que estos valores han sido validados y son inmutables.
    """
    provider: str  # "drand"
    round: int
    randomness_hex: str  # hex string (sin 0x)
    signature_hex: Optional[str] = None
    public_key_hex: Optional[str] = None
    round_time_utc: Optional[datetime] = None


@dataclass(frozen=True)
class _EngineResult:
    """
    Resultado interno compatible con adjudication_service_pro:
    - seed (hex)
    - inputs_hash (manifest_commit)
    - proof_hash
    - ranking (json-serializable)
    - awarded_participant_id
    """
    awarded_participant_id: str
    seed: str
    inputs_hash: str
    proof_hash: str
    ranking: Any
    engine_version: str
    algorithm_id: str


# ==========================================================
# 🔹 UTILIDADES CRIPTO / CANONICALIZACIÓN
# ==========================================================

def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(obj: Any) -> str:
    """
    JSON canónico (estable):
    - sort_keys True
    - separadores sin espacios
    - ensure_ascii False
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _dt_to_iso_z(dt: datetime) -> str:
    dt_utc = dt.astimezone(timezone.utc)
    # ISO8601 con Z final
    return dt_utc.replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ==========================================================
# 🔹 ENTRADAS DETERMINISTAS: EXPANSIÓN DE PARTICIPACIONES
# ==========================================================

def _expand_entries(participants: List[ParticipantSnapshot]) -> Tuple[List[str], Dict[str, str]]:
    """
    Convierte participantes con participations>1 en "entradas" deterministas.
    Devuelve:
    - entries_hashes: lista de hashes (hex) de cada entrada, ordenados canónicamente
    - entry_hash -> participant_id (para mapear idx a adjudicatario)
    """
    entry_to_participant: Dict[str, str] = {}
    entries: List[str] = []

    for p in participants:
        count = int(p.participations or 1)
        if count <= 0:
            continue
        # cada entrada deriva de participant_id + ordinal
        for i in range(count):
            entry_id = f"{p.participant_id}:{i}"
            entry_hash = _sha256_hex(entry_id.encode("utf-8"))
            entries.append(entry_hash)
            entry_to_participant[entry_hash] = p.participant_id

    # orden canónico para que el orden de llegada NO afecte
    entries.sort()
    return entries, entry_to_participant


# ==========================================================
# 🔹 MERKLE ROOT (SHA-256) SOBRE LISTA DE ENTRADAS
# ==========================================================

def _merkle_root_hex(leaves_hex_sorted: List[str]) -> str:
    """
    Merkle root determinista:
    - leaves_hex_sorted ya viene ordenado
    - cada leaf se interpreta como bytes de su hex
    - hash interno: SHA256(left || right)
    - si impar: duplica último
    """
    if not leaves_hex_sorted:
        return _sha256_hex(b"")

    # hojas como bytes
    level = [bytes.fromhex(h) for h in leaves_hex_sorted]

    while len(level) > 1:
        nxt: List[bytes] = []
        i = 0
        while i < len(level):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]  # duplica si impar
            nxt.append(hashlib.sha256(left + right).digest())
            i += 2
        level = nxt

    return level[0].hex()


# ==========================================================
# 🔹 MANIFEST + COMMIT
# ==========================================================

def _build_manifest(
    *,
    session: SessionSnapshot,
    entries_sorted: List[str],
    participants_count: int,
    context: DeterministicContext,
) -> Dict[str, Any]:
    """
    Manifiesto mínimo, suficiente para commit/auditoría:
    (alineado con anexos: session_id, timestamps, N, lista/merkle, terms/rules, etc.)
    """
    return {
        "schema_version": "manifest.v1",
        "session_id": session.session_id,
        "product_id": session.product_id,
        "session_created_at_utc": _dt_to_iso_z(session.session_created_at),
        "session_closed_at_utc": _dt_to_iso_z(session.session_closed_at),
        "capacity": int(session.capacity),
        "rules_version": str(session.rules_version),
        "participants_count": int(participants_count),
        "entries_count": int(len(entries_sorted)),
        # Guardamos lista completa de hojas (hashes) para verificación externa si se desea.
        # Si quisieras compactar, puedes publicar solo merkle_root y guardar lista internamente.
        "entries_hashes_sorted": entries_sorted,
        "engine_context": {
            "engine_version": getattr(context, "engine_version", ENGINE_VERSION_DEFAULT),
            "algorithm_id": getattr(context, "algorithm_id", ALGORITHM_ID_DEFAULT),
            "normalization": getattr(context, "normalization", "stable_sort_by_entry_hash"),
        },
    }


def _compute_manifest_commit(manifest: Dict[str, Any]) -> str:
    canon = _canonical_json(manifest)
    return _sha256_hex(canon.encode("utf-8"))


# ==========================================================
# 🔹 CÁLCULO SEED / ÍNDICE / RANKING
# ==========================================================

def _compute_seed_hex(
    *,
    session_id: str,
    participants_merkle_root: str,
    participants_count: int,
    manifest_commit: str,
    entropy: ExternalEntropySnapshot,
) -> Tuple[str, str]:
    """
    seed_input = session_id || participants_merkle_root || N || drand_round || drand_randomness || manifest_commit
    seed = SHA256(seed_input)
    (alineado con anexos)
    """
    seed_input = "|".join(
        [
            session_id,
            participants_merkle_root,
            str(participants_count),
            str(int(entropy.round)),
            str(entropy.randomness_hex),
            manifest_commit,
        ]
    )
    seed_hex = _sha256_hex(seed_input.encode("utf-8"))
    return seed_hex, seed_input


def _select_awarded(
    *,
    entries_sorted: List[str],
    entry_to_participant: Dict[str, str],
    seed_hex: str,
) -> Tuple[str, int, str]:
    """
    idx = int(seed_hex,16) mod N
    awarded_entry = entries_sorted[idx]
    awarded_participant_id = mapping[awarded_entry]
    """
    n = len(entries_sorted)
    if n <= 0:
        raise ValueError("No hay entradas elegibles (entries_count=0).")

    idx = int(seed_hex, 16) % n
    awarded_entry = entries_sorted[idx]
    awarded_participant_id = entry_to_participant[awarded_entry]
    return awarded_participant_id, idx, awarded_entry


def _build_ranking(
    *,
    participants: List[ParticipantSnapshot],
    seed_hex: str,
    awarded_participant_id: str,
) -> List[Dict[str, Any]]:
    """
    Ranking determinista auxiliar (para auditoría).
    score = SHA256(seed_hex || participant_id)
    Orden por score asc + participant_id (desempate)
    """
    rows: List[Dict[str, Any]] = []
    for p in participants:
        score = _sha256_hex(f"{seed_hex}|{p.participant_id}".encode("utf-8"))
        rows.append(
            {
                "participant_id": p.participant_id,
                "user_id": p.user_id,
                "participations": int(p.participations or 1),
                "score": score,
                "is_awarded": (p.participant_id == awarded_participant_id),
            }
        )

    rows.sort(key=lambda r: (r["score"], r["participant_id"]))
    # añade rank
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
    return rows


def _compute_proof_hash(proof_bundle: Dict[str, Any]) -> str:
    canon = _canonical_json(proof_bundle)
    return _sha256_hex(canon.encode("utf-8"))


# ==========================================================
# 🔹 API PÚBLICA DEL MOTOR (PURE FUNCTION)
# ==========================================================

def adjudicate(
    *,
    session: SessionSnapshot,
    participants: List[ParticipantSnapshot],
    context: DeterministicContext,
    external_entropy: ExternalEntropySnapshot,
) -> Any:
    """
    Motor determinista PRO alineado con documentación IP.
    Devuelve un objeto con atributos:
    - awarded_participant_id
    - ranking
    - seed
    - inputs_hash
    - proof_hash
    - engine_version
    - algorithm_id

    IMPORTANTE:
    - Terminología: awarded (no winner)
    - El motor NO hace llamadas externas (drand se obtiene/valida fuera)
    """
    if external_entropy is None:
        raise ValueError("external_entropy (drand) es obligatorio en modo PRO (alineación IP).")
    if external_entropy.provider.lower() != "drand":
        raise ValueError("Solo se soporta provider='drand' en esta versión PRO.")

    engine_version = getattr(context, "engine_version", ENGINE_VERSION_DEFAULT)
    algorithm_id = getattr(context, "algorithm_id", ALGORITHM_ID_DEFAULT)

    # 1) Entradas deterministas (independientes de orden de llegada)
    entries_sorted, entry_to_participant = _expand_entries(participants)
    participants_merkle_root = _merkle_root_hex(entries_sorted)
    participants_count = len(entries_sorted)

    # 2) Manifest + commit (inputs_hash)
    manifest = _build_manifest(
        session=session,
        entries_sorted=entries_sorted,
        participants_count=participants_count,
        context=context,
    )
    manifest_commit = _compute_manifest_commit(manifest)

    # 3) seed (según anexos: combina commit/merkle + drand_round/randomness)
    seed_hex, seed_input = _compute_seed_hex(
        session_id=session.session_id,
        participants_merkle_root=participants_merkle_root,
        participants_count=participants_count,
        manifest_commit=manifest_commit,
        entropy=external_entropy,
    )

    # 4) Selección determinista por módulo
    awarded_participant_id, awarded_index, awarded_entry = _select_awarded(
        entries_sorted=entries_sorted,
        entry_to_participant=entry_to_participant,
        seed_hex=seed_hex,
    )

    # 5) Ranking auxiliar + meta
    ranking_rows = _build_ranking(
        participants=participants,
        seed_hex=seed_hex,
        awarded_participant_id=awarded_participant_id,
    )

    ranking_payload: Dict[str, Any] = {
        "schema_version": "ranking.v1",
        "meta": {
            "session_id": session.session_id,
            "product_id": session.product_id,
            "engine_version": engine_version,
            "algorithm_id": algorithm_id,
            "manifest_commit": manifest_commit,
            "participants_merkle_root": participants_merkle_root,
            "entries_count": participants_count,
            "awarded_index": awarded_index,
            "awarded_entry_hash": awarded_entry,
            "seed_input": seed_input,
            "seed_hex": seed_hex,
            "drand": {
                "provider": external_entropy.provider,
                "round": int(external_entropy.round),
                "randomness_hex": external_entropy.randomness_hex,
                "signature_hex": external_entropy.signature_hex,
                "public_key_hex": external_entropy.public_key_hex,
                "round_time_utc": _dt_to_iso_z(external_entropy.round_time_utc)
                if external_entropy.round_time_utc
                else None,
            },
        },
        "participants": ranking_rows,
    }

    # 6) Proof bundle mínimo (auditable)
    proof_bundle: Dict[str, Any] = {
        "schema_version": "proof.v1",
        "created_at_utc": _dt_to_iso_z(datetime.now(timezone.utc)),
        "engine_version": engine_version,
        "algorithm_id": algorithm_id,
        "session": {
            "session_id": session.session_id,
            "product_id": session.product_id,
            "closed_at_utc": _dt_to_iso_z(session.session_closed_at),
        },
        "manifest_commit": manifest_commit,
        "participants_merkle_root": participants_merkle_root,
        "entries_count": participants_count,
        "drand": {
            "provider": external_entropy.provider,
            "round": int(external_entropy.round),
            "randomness_hex": external_entropy.randomness_hex,
            "signature_hex": external_entropy.signature_hex,
            "public_key_hex": external_entropy.public_key_hex,
            "round_time_utc": _dt_to_iso_z(external_entropy.round_time_utc)
            if external_entropy.round_time_utc
            else None,
        },
        "calculation": {
            "seed_input": seed_input,
            "seed_hex": seed_hex,
            "awarded_index": awarded_index,
        },
        "result": {
            "awarded_participant_id": awarded_participant_id,
        },
    }

    proof_hash = _compute_proof_hash(proof_bundle)

    # inputs_hash: alineado con tu documentación como “commit” del dataset (manifest_commit)
    inputs_hash = manifest_commit

    # Resultado compatible con adjudication_service_pro
    return _EngineResult(
        awarded_participant_id=awarded_participant_id,
        seed=seed_hex,
        inputs_hash=inputs_hash,
        proof_hash=proof_hash,
        ranking=ranking_payload,
        engine_version=engine_version,
        algorithm_id=algorithm_id,
    )
