# backend_core/engines/session_engine.py
from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ==============================================================================
# ESQUEMA DEFINITIVO (según tu aclaración)
# ==============================================================================
# ca_sessions (
#   id, product_id, module_id, status, created_at, closed_at, capacity,
#   rules_version, previous_session_id, previous_chain_hash
# )
#
# ca_participants (
#   id, session_id, user_id, participations, is_awarded, created_at
# )
#
# ca_adjudications (
#   id, session_id, winner_participant_id, ranking, seed, inputs_hash,
#   proof_hash, engine_version, algorithm_id, created_at
# )
# ==============================================================================

SESSIONS_TABLE = "ca_sessions"
PARTICIPANTS_TABLE = "ca_participants"
AUDIT_TABLE = os.getenv("CA_AUDIT_TABLE", "ca_audit_logs")  # best-effort, si existe

# Columnas en ca_sessions (definitivas)
COL_SESSION_ID = "id"
COL_PRODUCT_ID = "product_id"
COL_MODULE_ID = "module_id"
COL_STATUS = "status"
COL_CREATED_AT = "created_at"
COL_CLOSED_AT = "closed_at"
COL_CAPACITY = "capacity"
COL_RULES_VERSION = "rules_version"
COL_PREV_SESSION_ID = "previous_session_id"
COL_PREV_CHAIN_HASH = "previous_chain_hash"

# Columnas en ca_participants (definitivas)
COL_P_SESSION_ID = "session_id"
COL_P_PARTICIPATIONS = "participations"

# Status esperados (invariantes)
STATUS_PARKED = "parked"
STATUS_ACTIVE = "active"
STATUS_CLOSED = "closed"
STATUS_EXPIRED = "expired"
STATUS_FINISHED = "finished"

DEFAULT_MAX_DURATION_DAYS = 5


# ==============================================================================
# SUPABASE CLIENT
# ==============================================================================

def _get_supabase_client():
    """
    Devuelve un cliente de Supabase.
    - Primero intenta importar un helper del proyecto.
    - Si no existe, crea el cliente con SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY / SUPABASE_ANON_KEY.
    """
    # 1) Helper del proyecto (si existe)
    try:
        from backend_core.db.supabase_client import get_supabase  # type: ignore
        return get_supabase()
    except Exception:
        pass

    # 2) Crear cliente directo
    try:
        from supabase import create_client  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "No se pudo importar supabase-py. Instala 'supabase' o expón un helper backend_core.db.supabase_client.get_supabase()."
        ) from e

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Faltan SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY (o SUPABASE_ANON_KEY).")

    return create_client(url, key)


# ==============================================================================
# SESSION MODULE MANAGER
# ==============================================================================

def _get_module_manager():
    """
    Devuelve SessionModuleManager si está disponible.
    Asumimos que existe exactamente como el entregado.
    """
    try:
        from backend_core.services.session_module_manager import SessionModuleManager  # type: ignore
        return SessionModuleManager()
    except Exception:
        return None


# ==============================================================================
# ADJUDICATION SERVICE (disparo determinista)
# ==============================================================================

def _trigger_adjudication(session_id: str) -> Tuple[bool, str]:
    """
    Llama al adjudication_service_pro para adjudicar una sesión ya cerrada.
    Para minimizar fricción, prueba varios nombres comunes de función.
    """
    try:
        mod = __import__("backend_core.services.adjudication_service_pro", fromlist=["*"])
    except Exception as e:
        logger.exception("No se pudo importar adjudication_service_pro")
        return False, f"Import error adjudication_service_pro: {e!r}"

    candidates = [
        "adjudicate_session_pro",
        "run_adjudication_pro",
        "adjudicate_session",
        "adjudicate",
    ]

    for fn_name in candidates:
        fn = getattr(mod, fn_name, None)
        if callable(fn):
            try:
                # Soporta firma con keyword o posicional
                try:
                    fn(session_id=session_id)
                except TypeError:
                    fn(session_id)
                return True, f"adjudication_service_pro.{fn_name} OK"
            except Exception as e:
                logger.exception("Adjudication failed via %s for session_id=%s", fn_name, session_id)
                return False, f"Adjudication error via {fn_name}: {e!r}"

    return False, "No se encontró función de adjudicación en adjudication_service_pro (candidates no disponibles)."


# ==============================================================================
# MODELOS Y UTILS
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
    session_engine:
      - calcula filled_units (= SUM participations)
      - cierra por aforo exacto (idempotente)
      - expira por tiempo (created_at + duración módulo / default 5 días)
      - rolling solo si el módulo lo permite (crea sesión NUEVA en parked)
      - dispara adjudicación determinista cuando la sesión pasa a closed
    """

    def __init__(self, supabase=None, module_manager=None):
        self.sb = supabase or _get_supabase_client()
        self.module_manager = module_manager if module_manager is not None else _get_module_manager()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def run_once(self, limit: int = 500) -> Dict[str, Any]:
        """
        Procesa:
          1) Sesiones ACTIVE: cerrar si filled_units == capacity (o >= por seguridad, pero el invariante lo impide)
          2) Sesiones ACTIVE: expirar si vencidas y no completas
          3) Rolling: si expira y módulo permite, crea nueva sesión PARKED
        """
        metrics = {
            "active_scanned": 0,
            "closed": 0,
            "expired": 0,
            "rolled": 0,
            "adjudications_triggered": 0,
            "adjudications_failed": 0,
        }

        active = self._fetch_sessions_by_status(STATUS_ACTIVE, limit=limit)
        metrics["active_scanned"] = len(active)

        # 1) Cierre por aforo exacto
        for s in active:
            filled = self._get_filled_units(s.id)
            self._validate_invariants(s, filled)

            if filled >= s.capacity:
                changed = self._close_session_if_active(s.id)
                if changed:
                    metrics["closed"] += 1
                    ok, _msg = _trigger_adjudication(s.id)
                    if ok:
                        metrics["adjudications_triggered"] += 1
                    else:
                        metrics["adjudications_failed"] += 1

        # 2) Expiración
        active = self._fetch_sessions_by_status(STATUS_ACTIVE, limit=limit)  # refresco
        now = _utcnow()
        for s in active:
            filled = self._get_filled_units(s.id)
            self._validate_invariants(s, filled)

            # Si ya está completa, debería cerrarse arriba; aquí solo expira si NO completa
            if filled < s.capacity and self._is_expired(s, now=now):
                changed = self._expire_session_if_active(s.id)
                if changed:
                    metrics["expired"] += 1

                    # 3) Rolling si aplica
                    if self._module_supports_rolling(s.module_id):
                        rolled = self._roll_session(previous_session=s)
                        if rolled:
                            metrics["rolled"] += 1

        return metrics

    # ------------------------------------------------------------------
    # Fetch
    # ------------------------------------------------------------------

    def _fetch_sessions_by_status(self, status: str, limit: int = 500) -> List[SessionRow]:
        resp = (
            self.sb.table(SESSIONS_TABLE)
            .select(
                ",".join([
                    COL_SESSION_ID,
                    COL_PRODUCT_ID,
                    COL_MODULE_ID,
                    COL_STATUS,
                    COL_CAPACITY,
                    COL_CREATED_AT,
                    COL_CLOSED_AT,
                    COL_RULES_VERSION,
                    COL_PREV_SESSION_ID,
                    COL_PREV_CHAIN_HASH,
                ])
            )
            .eq(COL_STATUS, status)
            .limit(limit)
            .execute()
        )

        rows = getattr(resp, "data", None) or []
        out: List[SessionRow] = []
        for r in rows:
            out.append(
                SessionRow(
                    id=str(r.get(COL_SESSION_ID)),
                    product_id=r.get(COL_PRODUCT_ID),
                    module_id=r.get(COL_MODULE_ID),
                    status=str(r.get(COL_STATUS)),
                    capacity=_safe_int(r.get(COL_CAPACITY), 0),
                    created_at=_parse_dt(r.get(COL_CREATED_AT)),
                    closed_at=_parse_dt(r.get(COL_CLOSED_AT)),
                    rules_version=r.get(COL_RULES_VERSION),
                    previous_session_id=r.get(COL_PREV_SESSION_ID),
                    previous_chain_hash=r.get(COL_PREV_CHAIN_HASH),
                )
            )
        return out

    # ------------------------------------------------------------------
    # filled_units
    # ------------------------------------------------------------------

    def _get_filled_units(self, session_id: str) -> int:
        """
        SUM(ca_participants.participations) WHERE session_id = ?
        """
        resp = (
            self.sb.table(PARTICIPANTS_TABLE)
            .select(COL_P_PARTICIPATIONS)
            .eq(COL_P_SESSION_ID, session_id)
            .execute()
        )
        rows = getattr(resp, "data", None) or []
        total = 0
        for r in rows:
            total += _safe_int(r.get(COL_P_PARTICIPATIONS), 0)
        return total

    # ------------------------------------------------------------------
    # invariantes
    # ------------------------------------------------------------------

    def _validate_invariants(self, s: SessionRow, filled_units: int) -> None:
        if s.capacity <= 0:
            raise ValueError(f"[Invariant] capacity must be > 0 for session {s.id}")
        if filled_units < 0:
            raise ValueError(f"[Invariant] filled_units must be >= 0 for session {s.id}")
        if filled_units > s.capacity:
            # Esto NO debería pasar: si pasa, hay bug en control de participaciones.
            raise ValueError(
                f"[Invariant] filled_units ({filled_units}) > capacity ({s.capacity}) for session {s.id}"
            )

    # ------------------------------------------------------------------
    # expiración (sin expires_at en DB)
    # ------------------------------------------------------------------

    def _is_expired(self, s: SessionRow, now: Optional[datetime] = None) -> bool:
        now = now or _utcnow()
        if not s.created_at:
            return False
        days = self._module_max_duration_days(s.module_id)
        expires_at = s.created_at + timedelta(days=days)
        return now >= expires_at

    # ------------------------------------------------------------------
    # close/expire idempotentes (CAS por status)
    # ------------------------------------------------------------------

    def _close_session_if_active(self, session_id: str) -> bool:
        now = _utcnow().isoformat()
        resp = (
            self.sb.table(SESSIONS_TABLE)
            .update({COL_STATUS: STATUS_CLOSED, COL_CLOSED_AT: now})
            .eq(COL_SESSION_ID, session_id)
            .eq(COL_STATUS, STATUS_ACTIVE)
            .execute()
        )
        changed = bool(getattr(resp, "data", None))
        if changed:
            self._audit("session_closed", session_id=session_id, meta={"closed_at": now})
            logger.info("Session closed: %s", session_id)
        return changed

    def _expire_session_if_active(self, session_id: str) -> bool:
        now = _utcnow().isoformat()
        # No existe expired_at en tu esquema definitivo, así que NO lo escribimos.
        resp = (
            self.sb.table(SESSIONS_TABLE)
            .update({COL_STATUS: STATUS_EXPIRED})
            .eq(COL_SESSION_ID, session_id)
            .eq(COL_STATUS, STATUS_ACTIVE)
            .execute()
        )
        changed = bool(getattr(resp, "data", None))
        if changed:
            self._audit("session_expired", session_id=session_id, meta={"expired_at_logical": now})
            logger.info("Session expired: %s", session_id)
        return changed

    # ------------------------------------------------------------------
    # rolling (crea sesión NUEVA en PARKED)
    # ------------------------------------------------------------------

    def _roll_session(self, previous_session: SessionRow) -> bool:
        """
        Crea una nueva sesión limpia para el mismo product_id y module_id.
        Según tu modelo: la nueva sesión entra al parque => status = parked.
        """
        if not previous_session.product_id:
            logger.warning("Rolling skipped: missing product_id for session=%s", previous_session.id)
            return False

        created_at = _utcnow().isoformat()

        payload = {
            COL_PRODUCT_ID: previous_session.product_id,
            COL_MODULE_ID: previous_session.module_id,
            COL_STATUS: STATUS_PARKED,  # ✅ coherente con “parque de sesiones”
            COL_CAPACITY: previous_session.capacity,
            COL_CREATED_AT: created_at,
            COL_RULES_VERSION: previous_session.rules_version,
            COL_PREV_SESSION_ID: previous_session.id,
            COL_PREV_CHAIN_HASH: previous_session.previous_chain_hash,
        }

        resp = self.sb.table(SESSIONS_TABLE).insert(payload).execute()
        inserted = bool(getattr(resp, "data", None))
        if inserted:
            new_id = ""
            try:
                new_id = str(resp.data[0].get(COL_SESSION_ID, "")) if resp.data else ""
            except Exception:
                new_id = ""

            self._audit(
                "session_rolled",
                session_id=new_id or "unknown",
                meta={
                    "previous_session_id": previous_session.id,
                    "product_id": previous_session.product_id,
                    "module_id": previous_session.module_id,
                    "rules_version": previous_session.rules_version,
                },
            )
            logger.info("Session rolled: prev=%s new=%s", previous_session.id, new_id)

        return inserted

    # ------------------------------------------------------------------
    # module policies
    # ------------------------------------------------------------------

    def _module_supports_rolling(self, module_id: Optional[str]) -> bool:
        if not module_id:
            return False
        if not self.module_manager:
            # Por seguridad: si no hay manager, no hacemos rolling
            return False
        try:
            m = self.module_manager.get_module(module_id)  # type: ignore[attr-defined]
            return bool(getattr(m, "supports_rolling", False))
        except Exception:
            return False

    def _module_max_duration_days(self, module_id: Optional[str]) -> int:
        if not module_id or not self.module_manager:
            return DEFAULT_MAX_DURATION_DAYS
        try:
            m = self.module_manager.get_module(module_id)  # type: ignore[attr-defined]
            days = getattr(m, "max_duration_days", None)
            return int(days) if days is not None else DEFAULT_MAX_DURATION_DAYS
        except Exception:
            return DEFAULT_MAX_DURATION_DAYS

    # ------------------------------------------------------------------
    # audit (best-effort)
    # ------------------------------------------------------------------

    def _audit(self, event: str, session_id: str, meta: Optional[Dict[str, Any]] = None) -> None:
        try:
            payload = {
                "event": event,
                "session_id": session_id,
                "created_at": _utcnow().isoformat(),
                "meta": meta or {},
            }
            self.sb.table(AUDIT_TABLE).insert(payload).execute()
        except Exception:
            # No rompemos la ejecución por auditoría
            return


# ==============================================================================
# Función simple para worker/cron
# ==============================================================================

def process_sessions_once(limit: int = 500) -> Dict[str, Any]:
    engine = SessionEngine()
    return engine.run_once(limit=limit)
