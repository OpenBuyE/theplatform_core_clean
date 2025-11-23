"""
session_engine.py
Motor de gestión de sesiones Compra Abierta.

Responsabilidades:
- Procesar expiración de sesiones (5 días máx) sin aforo completo
- Marcar sesiones como finished sin adjudicación cuando expiran
- Activar la siguiente sesión de la serie (rolling) cuando:
    - una sesión expira sin adjudicación
    - una sesión se adjudica (llamado desde adjudicator_engine)
"""

from datetime import datetime
from typing import Dict, Optional, List

from .session_repository import session_repository
from .audit_repository import log_event


class SessionEngine:
    # ---------------------------------------------------------
    #  Procesar expiración de sesiones (job/worker)
    # ---------------------------------------------------------
    def process_expired_sessions(self) -> int:
        """
        Busca sesiones activas cuya expires_at < ahora
        y las marca como finished SIN adjudicación,
        activando la siguiente sesión parked en la serie.

        Devuelve el número de sesiones procesadas.
        """
        now_iso = datetime.utcnow().isoformat()
        expired_sessions: List[Dict] = session_repository.get_active_sessions_expired(now_iso)

        count = 0

        for s in expired_sessions:
            session_id = s["id"]

            # Marcar como finished sin adjudicación
            session_repository.mark_session_as_finished_without_award(
                session_id=session_id,
                finished_at=now_iso,
            )

            log_event(
                action="session_expired_without_award",
                session_id=session_id,
                metadata={
                    "expires_at": s.get("expires_at"),
                    "pax_registered": s.get("pax_registered"),
                    "capacity": s.get("capacity"),
                },
            )

            # Rolling: activar siguiente sesión en la serie
            self.activate_next_session_in_series(s)

            count += 1

        return count

    # ---------------------------------------------------------
    #  Rolling: activar siguiente sesión de la serie
    # ---------------------------------------------------------
    def activate_next_session_in_series(self, session: Dict) -> Optional[Dict]:
        """
        Dada una sesión (ya finished o a punto de finalizar),
        intenta activar la siguiente sesión parked de la misma serie.

        Devuelve la sesión activada o None.
        """
        next_session = session_repository.get_next_session_in_series(session)

        if not next_session:
            log_event(
                action="rolling_no_next_session_in_series",
                session_id=session.get("id"),
                metadata={
                    "series_id": session.get("series_id"),
                    "sequence_number": session.get("sequence_number"),
                },
            )
            return None

        activated = session_repository.activate_session(next_session["id"])

        log_event(
            action="rolling_next_session_activated",
            session_id=session.get("id"),
            metadata={
                "activated_session_id": activated["id"] if activated else None,
                "series_id": next_session.get("series_id"),
                "sequence_number": next_session.get("sequence_number"),
            },
        )

        return activated


# Instancia global
session_engine = SessionEngine()
