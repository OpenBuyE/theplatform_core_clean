"""
session_engine.py
Motor de expiración y rolling automático de sesiones.

Reglas implementadas:

1) Si una sesión active NO completa aforo antes de expires_at:
    -> se marca como finished sin adjudicación
    -> se activa la siguiente sesión parked de la misma serie

2) Si una sesión se adjudica (motor determinista), este módulo
   se usa para activar la siguiente sesión (rolling).

Este motor NO adjudica sesiones. Esa lógica está en adjudicator_engine.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional

from .session_repository import session_repository
from .audit_repository import log_event


class SessionEngine:

    # ============================================================
    #      MOTOR: EXPIRACIÓN DE SESIONES ACTIVE NO COMPLETADAS
    # ============================================================
    def process_expired_sessions(self):
        """
        Procesa todas las sesiones activas que han excedido expires_at.
        Si NO completaron su aforo, finaliza la sesión sin adjudicación
        y activa la siguiente de la serie.
        """

        now_iso = datetime.utcnow().isoformat()

        # 1. Obtener sesiones activas ya expiradas
        expired_sessions = session_repository.get_active_sessions_expired(now_iso)

        for session in expired_sessions:
            session_id = session["id"]

            # 2. Verificar si NO completaron aforo
            if session["pax_registered"] < session["capacity"]:

                # 2.1 Marcar sesión como finalizada SIN adjudicar
                session_repository.mark_session_as_finished_without_award(
                    session_id=session_id,
                    finished_at=now_iso
                )

                log_event(
                    action="session_expired_without_award",
                    session_id=session_id,
                    metadata={
                        "pax_registered": session["pax_registered"],
                        "capacity": session["capacity"],
                        "expires_at": session["expires_at"]
                    }
                )

                # 2.2 Rolling: activar la siguiente sesión de la serie
                self.activate_next_session_in_series(session)

            # Si completó aforo pero aun así aparece como expirada:
            # (caso extremo por desorden temporal)
            else:
                log_event(
                    action="session_expired_but_full_capacity",
                    session_id=session_id
                )

    # ============================================================
    #     MOTOR: ACTIVAR SIGUIENTE SESIÓN DE LA SERIE (ROLLING)
    # ============================================================
    def activate_next_session_in_series(self, session: Dict) -> Optional[Dict]:
        """
        Activa la siguiente sesión parked de la misma serie.
        sequence_number > sesión actual.
        """

        next_session = session_repository.get_next_session_in_series(session)
        if not next_session:
            log_event(
                action="no_next_session_in_series",
                session_id=session["id"],
                metadata={
                    "series_id": session.get("series_id"),
                    "sequence_number": session.get("sequence_number")
                }
            )
            return None

        # Activación estándar: duración 5 días desde ahora
        now = datetime.utcnow()
        expires_at = (now + timedelta(days=5)).isoformat()

        activated = session_repository.activate_session(
            session_id=next_session["id"],
            expires_at=expires_at
        )

        log_event(
            action="next_session_activated",
            session_id=next_session["id"],
            metadata={
                "series_id": session.get("series_id"),
                "previous_session_id": session["id"]
            }
        )

        return activated


# Instancia exportable
session_engine = SessionEngine()
