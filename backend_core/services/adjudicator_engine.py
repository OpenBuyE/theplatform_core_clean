"""
adjudicator_engine.py
Motor de adjudicación determinista de sesiones Compra Abierta.

Reglas fundamentales:
- Solo adjudica si AFORO = 100%
- Si la sesión está expirada → NO adjudica
- Selección determinista mediante:
    - seed pública (si existe)
    - seed interna derivada de la sesión
    - SHA256(seed efectiva) % capacity
- Tras adjudicar:
    - marca la sesión como finished
    - activa la siguiente sesión de la serie (rolling)
    - registra auditoría completa

IMPORTANTE: para evitar imports circulares,
este módulo NO importa participant_repository.
Trabaja directamente sobre la tabla session_participants vía supabase.
"""

import hashlib
from datetime import datetime

from .supabase_client import supabase
from .session_repository import session_repository
from .adjudicator_repository import adjudicator_repository
from .session_engine import session_engine
from .audit_repository import log_event


PARTICIPANT_TABLE = "session_participants"


class AdjudicatorEngine:

    # ================================================================
    #               MÉTODO PRINCIPAL DE ADJUDICACIÓN
    # ================================================================
    def adjudicate_session(self, session_id: str):
        """
        Ejecuta el motor determinista de adjudicación para una sesión concreta.
        Devuelve el participante ganador (dict) o None si no adjudica.
        """

        # ------------------------------------------------------------
        # 1. Cargar sesión
        # ------------------------------------------------------------
        session = session_repository.get_session_by_id(session_id)
        if not session:
            log_event(
                action="adjudication_error_session_not_found",
                session_id=session_id,
            )
            return None

        # ------------------------------------------------------------
        # 2. Validar precondiciones
        # ------------------------------------------------------------
        if session.get("status") != "active":
            log_event(
                action="adjudication_skipped_invalid_status",
                session_id=session_id,
                metadata={"status": session.get("status")},
            )
            return None

        if session.get("finished_at"):
            log_event(
                action="adjudication_skipped_already_finished",
                session_id=session_id,
            )
            return None

        if session.get("pax_registered") != session.get("capacity"):
            log_event(
                action="adjudication_skipped_incomplete_capacity",
                session_id=session_id,
                metadata={
                    "pax_registered": session.get("pax_registered"),
                    "capacity": session.get("capacity"),
                },
            )
            return None

        now_iso = datetime.utcnow().isoformat()
        expires_at = session.get("expires_at")

        if expires_at and expires_at <= now_iso:
            log_event(
                action="adjudication_skipped_already_expired",
                session_id=session_id,
                metadata={"expires_at": expires_at},
            )
            return None

        # ¿Ya hay adjudicatario?
        awarded_resp = (
            supabase.table(PARTICIPANT_TABLE)
            .select("id")
            .eq("session_id", session_id)
            .eq("is_awarded", True)
            .execute()
        )
        if awarded_resp.data:
            log_event(
                action="adjudication_skipped_already_awarded",
                session_id=session_id,
            )
            return None

        # ------------------------------------------------------------
        # 3. Cargar participantes
        # ------------------------------------------------------------
        participants_resp = (
            supabase.table(PARTICIPANT_TABLE)
            .select("*")
            .eq("session_id", session_id)
            .execute()
        )

        participants = participants_resp.data or []

        if len(participants) != session.get("capacity"):
            log_event(
                action="adjudication_error_capacity_mismatch",
                session_id=session_id,
                metadata={
                    "participants_len": len(participants),
                    "capacity": session.get("capacity"),
                },
            )
            return None

        # Orden determinista absoluta
        participants_sorted = sorted(
            participants,
            key=lambda p: (p.get("created_at"), p.get("id")),
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
        # 6. Calcular índice ganador
        # ------------------------------------------------------------
        winner_index = self._compute_winner_index(effective_seed, N)

        # ------------------------------------------------------------
        # 7. Seleccionar adjudicatario
        # ------------------------------------------------------------
        winner = participants_sorted[winner_index]

        # ------------------------------------------------------------
        # 8. Persistir adjudicación y cerrar sesión
        # ------------------------------------------------------------
        awarded_at = datetime.utcnow().isoformat()

        # 8.1 Marcar ganador en tabla de participantes
        (
            supabase.table(PARTICIPANT_TABLE)
            .update({"is_awarded": True, "awarded_at": awarded_at})
            .eq("id", winner["id"])
            .execute()
        )

        # 8.2 Marcar sesión como finished
        session_repository.mark_session_as_finished(
            session_id=session_id,
            finished_at=awarded_at,
        )

        # 8.3 Auditoría detallada
        log_event(
            action="session_adjudicated",
            session_id=session_id,
            user_id=winner.get("user_id"),
            organization_id=session.get("organization_id"),
            metadata={
                "winner_participant_id": winner.get("id"),
                "winner_user_id": winner.get("user_id"),
                "winner_index": winner_index,
                "capacity": session.get("capacity"),
                "participants_count": N,
                "public_seed": public_seed,
                "effective_seed": effective_seed,
                "hash_algorithm": "SHA256",
            },
        )

        # ------------------------------------------------------------
        # 9. Rolling: activar siguiente sesión
        # ------------------------------------------------------------
        session_engine.activate_next_session_in_series(session)

        return winner

    # ================================================================
    #               FUNCIONES AUXILIARES DEL MOTOR
    # ================================================================
    def _build_effective_seed(self, session: dict, public_seed: str | None) -> str:
        base = (
            f"SESSION:{session.get('id')}"
            f"|SERIES:{session.get('series_id')}"
            f"|SEQ:{session.get('sequence_number')}"
            f"|PRODUCT:{session.get('product_id')}"
            f"|ORG:{session.get('organization_id')}"
            f"|ACTIVATED_AT:{session.get('activated_at')}"
            f"|CAPACITY:{session.get('capacity')}"
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
