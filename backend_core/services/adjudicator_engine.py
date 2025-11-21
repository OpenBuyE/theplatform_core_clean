"""
adjudicator_engine.py
Motor determinista de adjudicación para Compra Abierta.

Reglas:
- Aforo debe estar al 100%
- Se adjudica inmediatamente
- No usa azar
- Selección determinista basada en orden / seed pública / hash
"""

from datetime import datetime
import hashlib

from .session_repository import session_repository
from .participant_repository import participant_repository
from .adjudicator_repository import adjudicator_repository
from .session_engine import session_engine
from .audit_repository import log_event


class AdjudicatorEngine:

    # ---------------------------------------------------------
    #  Fun: adjudicar una sesión completa
    # ---------------------------------------------------------
    def adjudicate_session(self, session_id: str):
        # 1. Obtener sesión
        session = session_repository.get_session_by_id(session_id)
        if not session:
            log_event(
                action="adjudication_error_session_not_found",
                session_id=session_id
            )
            return None

        # 2. Validar aforo completo
        if session["pax_registered"] != session["capacity"]:
            log_event(
                action="adjudication_error_not_full",
                session_id=session_id,
                metadata={"pax": session["pax_registered"], "capacity": session["capacity"]}
            )
            return None

        # 3. Obtener participantes
        participants = participant_repository.get_participants_by_session(session_id)
        if not participants:
            log_event(
                action="adjudication_error_no_participants",
                session_id=session_id
            )
            return None

        # 4. Obtener seed pública si existe
        public_seed = adjudicator_repository.get_public_seed_for_session(session_id)

        # 5. Selección determinista
        #
        # A falta del motor avanzado con hashing público,
        # aplicamos esta regla estable:
        #
        # - si NO hay seed → ganador = primer participante
        # - si hay seed → hash(seed + session_id) % total
        #
        if not public_seed:
            winner = participants[0]

        else:
            seed_input = (public_seed + session_id).encode("utf-8")
            hashed = hashlib.sha256(seed_input).hexdigest()
            index = int(hashed, 16) % len(participants)
            winner = participants[index]

        # 6. Marcar ganador en BD
        awarded_at = datetime.utcnow().isoformat()

        participant_repository.mark_as_awarded(
            participant_id=winner["id"],
            awarded_at=awarded_at
        )

        # 7. Marcar sesión como finalizada
        session_repository.mark_session_as_finished(
            session_id=session_id,
            finished_at=awarded_at
        )

        # 8. Activar siguiente sesión (rolling)
        session_engine.activate_next_session_in_series(session)

        # 9. Logging
        log_event(
            action="adjudication_success",
            session_id=session_id,
            metadata={
                "winner": winner["id"],
                "seed_used": public_seed,
                "total_participants": len(participants)
            }
        )

        return winner


# Instancia global
adjudicator_engine = AdjudicatorEngine()
