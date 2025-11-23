# backend_core/services/audit_repository.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from backend_core.services import supabase_client


class AuditRepository:
    """
    Abstracción simple para registrar auditoría en ca_audit_logs.
    Úsala desde:
      - contract_engine
      - wallet_orchestrator
      - fintech_routes (si hace falta)
      - session_engine / adjudicator_engine (si quieres dejar rastro alto nivel)
    """

    def log(
        self,
        action: str,
        session_id: Optional[str],
        user_id: Optional[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        payload = {
            "action": action,
            "session_id": session_id,
            "user_id": user_id,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
        }

        supabase_client.table("ca_audit_logs").insert(payload).execute()
