"""
adjudicator_engine.py
Motor determinista de adjudicación de Compra Abierta.

Optimizado para evitar imports circulares.
"""

import hashlib
from datetime import datetime
from typing import Dict, List, Optional

from .supabase_client import supabase
from .session_repository import session_repository
from .adjudicator_repository import adjudicator_repository
from .session_engine import session_engine
from .audit_repository import log_event


PARTICIPANT_TABLE = "session_participants"


class AdjudicatorEngine:
    # ---------------------------------------------------------
    #  Entrada principal: adjudicar una sesión
    # ---------------------------------------------------------
    def adjudicate_session(self, session_id: str) -> Optional[Dict]:

        # 1) Cargar sesión
        session = session_repository.get_session_by_id(session_id)
        if not session:
            log_event(
                action="adjudication_error_session_not_found",
                session_id=session_id
            )
            return None

        if session["status"] != "active":
            log_event(
                action="adjudication_skipped_session_not_active",
                session_id=session_id,
                metadata={"status": session["status"]}
            )
            return None

        # 2) Participantes
        participants = self._get_participants(session_id)
        if not participants:
            log_event(
                action="adjudication_error_no_participants",
                session_id=session_id
            )
            return None

        # 3) Aforo completo
        capacity = session["capacity"]
        pax_registered = session.get("pax_registered", len(participants))

        if pax_registered != capacity or len(participants) != capacity:
            log_event(
                action="adjudication_skipped_incomplete_capacity",
                session_id=session_id,
                metadata={
                    "pax_registered": pax_registered,
                    "participants_count": len(participants),
                    "capacity": capacity,
                }
            )
            return None

        # 4) No expirada
        now_iso = datetime.utcnow().isoformat()
        expires_at = session.get("expires_at")
        if expires_at and expires_at < now_iso:
            log_event(
                action="adjudication_skipped_session_expired",
                session_id=session_id,
                metadata={"expires_at": expires_at}
            )
            return None

        # 5) Índice determinista
        index = self._compute_deterministic_index(session, participants)
        awarded_participant = participants[index]

        # 6) Marcar adjudicatario
        awarded_at = now_iso
        self._mark_participant_awarded(awarded_participant["id"], awarded_at)

        # 7) Finalizar sesión
        session_repository.mark_session_as_finished(session_id, now_iso)

        log_event(
            action="session_adjudicated",
            session_id=session_id,
            user_id=awarded_participant["user_id"],
            metadata={
                "awarded_participant_id": awarded_participant["id"],
                "index": index,
                "capacity": capacity
            }
        )

        # 8) Rolling
        session_engine.activate_next_session_in_series(session)

        # 9) MOTOR CONTRACTUAL (import diferido → evita import circular)
        from .contract_engine import contract_engine
        contract_engine.on_session_awarded(
            session=session,
            participants=participants,
            awarded_participant=awarded_participant,
        )

        return awarded_participant

    # ---------------------------------------------------------
    def _get_participants(self, session_id: str) -> List[Dict]:
        response = (
            supabase
            .table(PARTICIPANT_TABLE)
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", asc=True)
            .execute()
        )
        return response.data or []

    # ---------------------------------------------------------
    def _mark_participant_awarded(self, participant_id: str, awarded_at: str) -> None:
        (
            supabase
            .table(PARTICIPANT_TABLE)
            .update({
                "is_awarded": True,
                "awarded_at": awarded_at
            })
            .eq("id", participant_id)
            .execute()
        )

        log_event(
            action="participant_marked_awarded",
            metadata={"participant_id": participant_id, "awarded_at": awarded_at}
        )

    # ---------------------------------------------------------
    def _compute_deterministic_index(self, session: Dict, participants: List[Dict]) -> int:

        session_id = session["id"]
        series_id = session.get("series_id") or ""
        sequence_number = session.get("sequence_number") or 0

        # Seed pública admin
        public_seed = adjudicator_repository.get_public_seed_for_session(session_id)
        public_seed_str = public_seed or ""

        participant_ids = [p["id"] for p in participants]

        base_material = "|".join([
            session_id,
            series_id,
            str(sequence_number),
            "|".join(participant_ids),
        ])

        combined = public_seed_str + "|" + base_material
        digest = hashlib.sha256(combined.encode("utf-8")).hexdigest()
        value = int(digest, 16)

        capacity = session["capacity"]
        index = value % capacity

        log_event(
            action="adjudication_seed_computed",
            session_id=session_id,
            metadata={
                "public_seed": public_seed_str,
                "base_material_hash": hashlib.sha256(base_material.encode("utf-8")).hexdigest(),
                "digest": digest,
                "value_mod_capacity": index,
                "capacity": capacity,
            }
        )

        return index


# Instancia global
adjudicator_engine = AdjudicatorEngine()
