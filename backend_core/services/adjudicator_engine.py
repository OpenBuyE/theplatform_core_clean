# backend_core/services/adjudicator_engine.py

import hashlib
from datetime import datetime
from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event
from backend_core.services.session_repository import (
    get_session_by_id,
    mark_session_finished,
    get_participants_sorted,
)
from backend_core.services.operator_repository import get_operator_global_seed


# ==========================================================================
# FUNCIONES INTERNAS
# ==========================================================================
def _build_input_string(session, num_participants: int, previous_hash: str):
    return (
        f"{session['id']}:"
        f"{session.get('module_id','')}:"
        f"{session['created_at']}:"
        f"{num_participants}:"
        f"{session.get('global_seed','')}:"
        f"{previous_hash}"
    )


def _calculate_hash(input_string: str):
    return hashlib.sha256(input_string.encode()).hexdigest()


# ==========================================================================
# API PRINCIPAL — USADA POR Active Sessions y Workers
# ==========================================================================
def run_adjudication(session_id: str):
    """
    Motor determinista:
    - carga sesión
    - carga participantes ordenados
    - genera semilla
    - calcula índice ganador
    - registra auditoría
    - marca sesión como terminada
    """
    session = get_session_by_id(session_id)
    if not session:
        raise Exception(f"Session {session_id} not found")

    participants = get_participants_sorted(session_id)
    num = len(participants)
    if num == 0:
        raise Exception("No participants found")

    previous_hash = session.get("previous_chain_hash") or ""

    input_string = _build_input_string(session, num, previous_hash)
    seed = _calculate_hash(input_string)

    winner_index = int(seed, 16) % num
    winner = participants[winner_index]

    # ============================================================
    # Registrar auditoría
    # ============================================================
    log_event(
        event_type="session_adjudicated",
        details={
            "session_id": session_id,
            "input_string": input_string,
            "hash_output": seed,
            "winner_participant_id": winner["id"],
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    # ============================================================
    # Actualizar participante ganador
    # ============================================================
    table("session_participants").update({"is_awarded": True}).eq("id", winner["id"]).execute()

    # ============================================================
    # Cambiar estado de sesión
    # ============================================================
    mark_session_finished(session_id)

    return {
        "winner_participant_id": winner["id"],
        "hash": seed,
        "input": input_string,
    }
