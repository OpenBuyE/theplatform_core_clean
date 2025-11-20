"""
adjudicator_engine.py
Motor de adjudicación determinista de sesiones Compra Abierta.

Reglas fundamentales aplicadas aquí:
- La adjudicación sólo ocurre cuando AFORO = 100%
- Si la sesión no completó aforo antes de expires_at → NO se adjudica
- El adjudicatario se selecciona de forma determinista mediante:
    - seed pública (si existe)
    - seed interna reproducible
    - SHA256(seed efectiva) % capacity
- Tras adjudicar:
    - la sesión se marca como finished
    - se activa la siguiente sesión de la serie (rolling)
    - se registra auditoría completa y verificable
"""

import hashlib
from datetime import datetime
from .session_repository import session_repository
from .participant_repository import participant_repository
from .adjudicator_repository import adjudicator_repository
from .session_engine import session_engine
from .audit_repository import log_event


class AdjudicatorEngine:

    # ================================================================
    #               MÉTODO PRINCIPAL DE ADJUDICACIÓN
    # ================================================================
    def adjudicate_session(self, session_id: str):
        """
        Motor determinista completo.
        """

        # ------------------------------------------------------------
        # 1. Cargar sesión
        # ------------------------------------------------------------
        session = session_repository.get_session_by_id(session_id)
        if not session:
            log_event(
                action="adjudication_error_session_not_found",
                session_id=session_id
            )
            return None

        # ------------------------------------------------------------
        # 2. Validar precondiciones
        # ------------------------------------------------------------
        if session["status"] != "active":
            log_event(
                action="adjudication_skipped_invalid_status",
                session_id=session_id,
                metadata={"status": session["status"]}
            )
            return None

        if session.get("finished_at"):
            log_event(
                action="adjudication_skipped_already_finished",
                session_id=session_id
            )
            return None

        if session["pax_registered"] != session["capacity"]:
            log_event(
                action="adjudication_skipped_incomplete_capacity",
                session_id=session_id,
                metadata={
                    "pax_registered": session["pax_registered"],
                    "capacity": session["capacity"]
                }
            )
            return None

        if session["expires_at"] <= datetime.utcnow().isoformat():
            log_event(
                action="adjudication_skipped_already_expired",
                session_id=session_id,
                metadata={"expires_at": session["expires_at"]}
            )
            return None

        if participant_repository.exists_awarded_participant(session_id):
            log_event(
                action="adjudication_skipped_already_awarded",
                session_id=session_id
            )
            return None

        # ------------------------------------------------------------
        # 3. Cargar participantes
        # ------------------------------------------------------------
        participants = participant_repository.get_participants_by_session(session_id)

        if len(participants) != session["capacity"]:
            log_event(
                action="adjudication_error_capacity_mismatch",
                session_id=session_id,
                metadata={
                    "participants_len": len(participants),
                    "capacity": session["capacity"]
                }
            )
            return None

        # Orden determinista absoluta
        participants_sorted = sorted(
            participants,
            key=lambda p: (p["created_at"], p["id"])
        )

        N = len(participants_sorted)

        # ------------------------------------------------------------
        # 4. Obtener semilla pública si existe
        # ------------------------------------------------------------
        public_seed = adjudicator_repository.get_public_seed_for_session(session_id)

        # ------------------------------------------------------------
        # 5. Construir semilla efectiva
        # ------------------------------------------------------------
        effective_seed = self._build_effective_seed(session, public_seed)

        # ------------------------------------------------------------
        # 6. Calcular el índice ganador determinista
        # ------------------------------------------------------------
        winner_index = self._compute_winner_index(effective_seed, N)

        # ------------------------------------------------------------
        # 7. Seleccionar adjudicatario
        # ------------------------------------------------------------
        winner = participants_sorted[winner_index]

        # ------------------------------------------------------------
        # 8. Guardar adjudicación y cerrar sesión
        # ------------------------------------------------------------
        now = datetime.utcnow().isoformat()

        participant_repository.mark_as_awarded(
            participant_id=winner["id"],
            awarded_at=now
        )

        session_repository.mark_session_as_finished(
            session_id=session_id,
            finished_at=now
        )

        # ------------------------------------------------------------
        # 9. Auditoría completa y trazable
        # ------------------------------------------------------------
        log_event(
            action="session_adjudicated",
            session_id=session_id,
            user_id=winner["user_id"],
            organization_id=session["organization_id"],
            metadata={
                "winner_participant_id": winner["id"],
                "winner_user_id": winner["user_id"],
                "winner_index": winner_index,
                "capacity": session["capacity"],
                "participants_count": N,
                "public_seed": public_seed,
                "effective_seed": effective_seed,
                "hash_algorithm": "SHA256"
            }
        )

        # ------------------------------------------------------------
        # 10. Rolling: activar siguiente sesión
        # ------------------------------------------------------------
        session_engine.activate_next_session_in_series(session)

        return winner

    # ================================================================
    #               FUNCIONES AUXILIARES DEL MOTOR
    # ================================================================
    def _build_effective_seed(self, session, public_seed: str | None) -> str:
        base = (
            f"SESSION:{session['id']}"
            f"|SERIES:{session['series_id']}"
            f"|SEQ:{session['sequence_number']}"
            f"|PRODUCT:{session['product_id']}"
            f"|ORG:{session['organization_id']}"
            f"|ACTIVATED_AT:{session['activated_at']}"
            f"|CAPACITY:{session['capacity']}"
        )

        if public_seed:
            return f"PUBLIC:{public_seed}|BASE:{base}"

        return f"BASE_ONLY:{base}"

    def _compute_winner_index(self, seed: str, N: int) -> int:
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        bigint = int(digest, 16)
        return bigint % N


# Instancia exportable
adjudicator_engine = AdjudicatorEngine()
