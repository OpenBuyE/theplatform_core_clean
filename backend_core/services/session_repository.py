from typing import List, Optional
from datetime import datetime
from backend_core.models.session import Session


class SessionRepository:
    """
    Repositorio en memoria para gestionar sesiones.
    Luego se reemplazará por Supabase.
    """

    def __init__(self):
        self.sessions: List[Session] = []

    def add(self, session: Session):
        self.sessions.append(session)

    def get_all(self) -> List[Session]:
        return list(self.sessions)

    def get_by_id(self, session_id: str) -> Optional[Session]:
        return next((s for s in self.sessions if s.id == session_id), None)

    def get_by_status(self, status: str) -> List[Session]:
        return [s for s in self.sessions if s.status == status]

    def activate(self, session_id: str) -> bool:
        session = self.get_by_id(session_id)
        if not session:
            return False
        session.status = "active"
        session.activated_at = datetime.utcnow()
        return True

    def schedule(self, session_id: str, when: datetime) -> bool:
        session = self.get_by_id(session_id)
        if not session:
            return False
        session.status = "scheduled"
        session.scheduled_for = when
        return True

    def close(self, session_id: str) -> bool:
        session = self.get_by_id(session_id)
        if not session:
            return False
        session.status = "closed"
        session.closed_at = datetime.utcnow()
        return True
