# backend_core/engines/session_engine.py
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event
from backend_core.services.adjudication_service_pro import adjudicate_session_pro

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ==============================================================================
# ESQUEMA REAL CONFIRMADO
# ==============================================================================
# ca_sessions (
#   id, product_id, module_id, status, created_at, closed_at, capacity,
#   rules_version, previous_session_id, previous_chain_hash
# )
#
# ca_session_participants (
#   id, session_id, user_id, organization_id,
#   amount, price, quantity,
#   is_awarded, awarded_at, created_at
# )
# ==============================================================================

SESSIONS_TABLE = "ca_sessions"
PARTICIPANTS_TABLE = "ca_session_participants"

STATUS_PARKED = "parked"
STATUS_ACTIVE = "active"
STATUS_CLOSED = "closed"
STATUS_EXPIRED = "expired"

SESSION_DURATION_DAYS = 5


# ==============================================================================
# MODELOS
# ==============================================================================

@dataclass(frozen=True)
class SessionRow:
    id: str
    product_id: Optional[str]
    module_id: Optional[str]
    status: str
    capacity: int
    created_at: Optional[datetime]
    closed_at: Optional[datetime]
    rules_version: Optional[str]
    previous_session_id: Optional[str]
    previous_chain_hash: Optional[str]


# ==============================================================================
# UTILS
# ==============================================================================

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        s = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


# ==============================================================================
# ENGINE
# ==============================================================================

class SessionEngine:
    """
    Engine de ciclo de vida de sesiones:
    - calcula aforo (SUM quantity)
    - cierra por aforo exacto
    - expira por tiempo (created_at + 5 días)
    - dispara adjudicación determinista PRO
    """

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def run_once(self, limit: int = 500) -> Dict[str, Any]:
        metrics = {
            "active_scanned": 0,
            "closed": 0,
            "expired": 0,
            "adjudications_triggered": 0,
        }

        active = self._fetch_sessions_by_status(STATUS_ACTIVE, limit)
        metrics["active_scanned"] = len(active)

        # 1) CIERRE POR AFORO
        for s in active:
            filled = self._get_filled_units(s.id)
            self._validate_invariants(s, filled)

            if filled >= s.capacity:
                changed = self._close_session_if_active(s.id)
                if changed:
                    metrics["closed"] += 1
                    adjudicate_session_pro(s.id)
                    metrics["adjudications_triggered"] += 1

        # 2) EXPIRACIÓN
        now = _utcnow()
        active = self._fetch_sessions_by_status(STATUS_ACTIVE, limit)
        for s in active:
            filled = self._get_filled_units(s.id)
            self._validate_invariants(s, filled)

            if filled < s.capacity and self._is_expired(s, now):
                changed = self._expire_session_if_active(s.id)
                if changed:
                    metrics["expired"] += 1

        return metrics

    # ------------------------------------------------------------------
    # FETCH
    # ------------------------------------------------------------------

    def _fetch_sessions_by_status(self, status: str, limit: int) -> List[SessionRow]:
        resp = (
            table(SESSIONS_TABLE)
            .select(
                "id, product_id, module_id, status, capacity, created_at, closed_at, "
                "rules_version, previous_session_id, previous_chain_hash"
            )
            .eq("status", status)
            .limit(limit)
            .execute()
        )

        rows = resp.data or []
        out: List[SessionRow] = []

        for r in rows:
            out.append(
                SessionRow(
                    id=str(r["id"]),
                    product_id=r.get("product_id"),
                    module_id=r.get("module_id"),
                    status=r["status"],
                    capacity=_safe_int(r.get("capacity")),
                    created_at=_parse_dt(r.get("created_at")),
                    closed_at=_parse_dt(r.get("closed_at")),
                    rules_version=r.get("rules_version"),
                    previous_session_id=r.get("previous_session_id"),
                    previous_chain_hash=r.get("previous_chain_hash"),
                )
            )
        return out

    # ------------------------------------------------------------------
    # AFORO REAL
    # ------------------------------------------------------------------

    def _get_filled_units(self, session_id: str) -> int:
        rows = (
            table(PARTICIPANTS_TABLE)
            .select("quantity")
            .eq("session_id", session_id)
            .execute()
            .data
            or []
        )

        total = 0
        for r in rows:
            total += _safe_int(r.get("quantity"))

        return total

    # ------------------------------------------------------------------
    # INVARIANTES
    # ------------------------------------------------------------------

    def _validate_invariants(self, s: SessionRow, filled: int) -> None:
        if s.capacity <= 0:
            raise ValueError(f"capacity inválida en sesión {s.id}")
        if filled < 0:
            raise ValueError(f"filled_units negativo en sesión {s.id}")
        if filled > s.capacity:
            raise ValueError(f"filled_units > capacity en sesión {s.id}")

    # ------------------------------------------------------------------
    # EXPIRACIÓN
    # ------------------------------------------------------------------

    def _is_expired(self, s: SessionRow, now: datetime) -> bool:
        if not s.created_at:
            return False
        return now >= s.created_at + timedelta(days=SESSION_DURATION_DAYS)

    # ------------------------------------------------------------------
    # TRANSICIONES IDÉMPOTENTES
    # ------------------------------------------------------------------

    def _close_session_if_active(self, session_id: str) -> bool:
        now = _utcnow().isoformat()
        resp = (
            table(SESSIONS_TABLE)
            .update({"status": STATUS_CLOSED, "closed_at": now})
            .eq("id", session_id)
            .eq("status", STATUS_ACTIVE)
            .execute()
        )
        if resp.data:
            log_event("session_closed", session_id, {"closed_at": now})
            logger.info("Session closed: %s", session_id)
            return True
        return False

    def _expire_session_if_active(self, session_id: str) -> bool:
        resp = (
            table(SESSIONS_TABLE)
            .update({"status": STATUS_EXPIRED})
            .eq("id", session_id)
            .eq("status", STATUS_ACTIVE)
            .execute()
        )
        if resp.data:
            log_event("session_expired", session_id, {})
            logger.info("Session expired: %s", session_id)
            return True
        return False


# ==============================================================================
# ENTRYPOINT SIMPLE
# ==============================================================================

def process_sessions_once(limit: int = 500) -> Dict[str, Any]:
    return SessionEngine().run_once(limit)
