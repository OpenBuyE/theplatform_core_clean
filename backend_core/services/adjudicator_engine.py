import hashlib
import datetime
from backend_core.services.supabase_client import table
from backend_core.services.session_repository import (
    get_participants_sorted,
    finish_session,
    get_session_by_id,
)
from backend_core.services.audit_repository import log_event


# =====================================================
# 🔹 Helpers internos — construcción de seed
# =====================================================

def _build_seed_input(session: dict, num_participants: int) -> str:
    """
    Construye el string determinista que se usará como input del SHA256.
    Sigue la filosofía del PROMPT 4.
    """
    session_id = session.get("id", "") or session.get("session_id", "")
    module_id = (
        session.get("module_id")
        or session.get("module_id_fk")
        or ""
    )
    created_at = session.get("created_at", "")
    global_seed = (
        session.get("global_seed")
        or "DEFAULT_GLOBAL_SEED"
    )
    previous_chain_hash = (
        session.get("previous_chain_hash")
        or ""
    )

    return (
        f"{session_id}:"
        f"{module_id}:"
        f"{created_at}:"
        f"{num_participants}:"
        f"{global_seed}:"
        f"{previous_chain_hash}"
    )


def _compute_seed_hash(seed_input: str) -> str:
    """
    Aplica SHA256 al input determinista.
    """
    return hashlib.sha256(seed_input.encode()).hexdigest()


# =====================================================
# 🔹 API pública legacy — get_seed_for_session
# =====================================================

def get_seed_for_session(session_id: str):
    """
    Devuelve la seed (hash SHA256 hex) asociada a una sesión.
    Compatible con Engine Monitor y vistas legacy.
    """
    session = get_session_by_id(session_id)
    if not session:
        return None

    participants = get_participants_sorted(session_id)
    num = len(participants) if participants else 0

    seed_input = _build_seed_input(session, num)
    seed_hash = _compute_seed_hash(seed_input)
    return seed_hash


# =====================================================
# 🔹 Estado del motor — Engine Monitor
# =====================================================

def get_engine_state():
    """
    Snapshot del estado del motor determinista.
    Usado por Engine Monitor.
    """
    now = datetime.datetime.utcnow().isoformat()
    return {
        "engine": "deterministic_adjudicator",
        "version": "2.0",
        "status": "online",
        "timestamp": now,
    }


# =====================================================
# 🔹 Registro de adjudicación — usado por Session Chains / History
# =====================================================

def get_adjudication_record(session_id: str):
    """
    Devuelve el último registro de adjudicación para una sesión.
    Si no existe, devuelve una estructura legacy compatible.
    """
    try:
        result = (
            table("audit_log")
            .select("*")
            .eq("session_id", session_id)
            .eq("event_type", "session_adjudicated")
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )
        logs = result if isinstance(result, list) else result.get("data", [])
        if not logs:
            # Fallback legacy
            return {
                "session_id": session_id,
                "seed": None,
                "algorithm": "deterministic_v2",
                "status": "not_found",
                "details": "No adjudication log found",
            }

        rec = logs[0]
        extra = rec.get("extra") or {}
        seed = extra.get("seed") or extra.get("seed_hash") or extra.get("seed_input")
        hash_output = extra.get("hash_output")
        winner_id = extra.get("winner_participant_id") or extra.get("winner_id")

        return {
            "session_id": session_id,
            "seed": seed,
            "hash_output": hash_output,
            "winner_id": winner_id,
            "algorithm": extra.get("algorithm", "deterministic_v2"),
            "status": "completed",
            "raw": rec,
        }
    except Exception:
        # Fallback muy defensivo
        return {
            "session_id": session_id,
            "seed": None,
            "algorithm": "deterministic_v2",
            "status": "error",
            "details": "Error retrieving adjudication record",
        }


# =====================================================
# 🔹 Motor determinista principal (patent–ready)
# =====================================================

def run_adjudication(session_id: str):
    """
    Ejecuta la adjudicación determinista para una sesión.

    Algoritmo:
        1) Cargar sesión + participantes ordenados.
        2) Construir seed_input determinista:
            f"{session_id}:{module_id}:{created_at}:{num_participants}:{global_seed}:{previous_chain_hash}"
        3) seed_hash = SHA256(seed_input)
        4) winner_index = int(seed_hash, 16) % num_participants
        5) winner = participants[winner_index]
        6) Registrar todo en audit_log.
    """

    # 1) Cargar sesión
    session = get_session_by_id(session_id)
    if not session:
        raise Exception(f"Sesión {session_id} no encontrada.")

    # 2) Participantes ordenados
    participants = get_participants_sorted(session_id)
    if not participants:
        raise Exception("No hay participantes en la sesión.")

    num = len(participants)

    # 3) Construir seed_input y hash
    seed_input = _build_seed_input(session, num)
    seed_hash = _compute_seed_hash(seed_input)

    # 4) Índice ganador
    winner_index = int(seed_hash, 16) % num
    winner = participants[winner_index]

    # 5) Marcar ganador en ca_participants / ca_session_participants
    #    (usamos ca_session_participants por consistencia con la arquitectura actual)
    table("ca_session_participants")\
        .update({"is_awarded": True})\
        .eq("id", winner["id"])\
        .execute()

    # 6) Marcar sesión como finalizada
    finish_session(session_id)

    # 7) Log matemático en audit_log
    extra_payload = {
        "algorithm": "deterministic_v2",
        "seed_input": seed_input,
        "seed_hash": seed_hash,
        "winner_participant_id": winner["id"],
        "participants_total": num,
    }

    log_event(
        "session_adjudicated",
        session_id=session_id,
        extra=extra_payload,
    )

    # 8) Devolver resultado estructurado
    return {
        "session_id": session_id,
        "winner_participant_id": winner["id"],
        "winner_index": winner_index,
        "seed_input": seed_input,
        "seed_hash": seed_hash,
        "participants_total": num,
    }
