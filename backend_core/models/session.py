"""
session.py
Dominio de Sesiones de Compra Abierta.

Este módulo define el "Session Domain Model", es decir,
la representación limpia en código de una sesión de Compra Abierta,
independiente de Supabase / Streamlit / FastAPI.

Mapea directamente a la tabla:
  public.ca_sessions

Esquema actual de ca_sessions (resumen):

  id              uuid (PK)
  product_id      text
  organization_id uuid
  series_id       uuid
  sequence_number int
  status          text        -- 'parked' | 'active' | 'finished' | ...
  capacity        int         -- aforo obligatorio
  pax_registered  int         -- número de participantes registrados
  activated_at    timestamptz
  expires_at      timestamptz
  finished_at     timestamptz
  created_at      timestamptz

Reglas clave de dominio:
- capacity > 0 (aforo obligatorio)
- 0 <= pax_registered <= capacity
- status controla el ciclo: parked -> active -> finished
- expiración máxima 5 días (regla aplicada en motores, no aquí)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any, Dict


# =========================================================
# ENUMS DE DOMINIO
# =========================================================

class SessionStatus(str, Enum):
    """
    Estados principales del ciclo de vida de una sesión.
    (Valores almacenados en ca_sessions.status)
    """
    PARKED = "parked"
    ACTIVE = "active"
    FINISHED = "finished"
    # Opcionales / futuros:
    CANCELLED = "cancelled"
    # EXPIRED_WITHOUT_AWARD = "expired_without_award"  # si más adelante diferenciamos


# =========================================================
# MODELO DE SESIÓN
# =========================================================

@dataclass
class Session:
    """
    Dominio de Sesión de Compra Abierta.

    Representa una fila de public.ca_sessions, pero con tipos fuertes
    y métodos de ayuda para la lógica de negocio.
    """

    # Identidad y relaciones
    id: str
    product_id: str
    organization_id: str
    series_id: Optional[str] = None
    sequence_number: Optional[int] = None

    # Estado de sesión
    status: SessionStatus = SessionStatus.PARKED
    capacity: int = 0
    pax_registered: int = 0

    # Tiempos
    activated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    # Campo extensible para metadatos (no persistido directamente)
    # útil para adjuntar info de producto, serie, etc. en memoria
    extra: Dict[str, Any] = field(default_factory=dict)

    # -----------------------------------------------------
    # CONSTRUCTORES DE AYUDA
    # -----------------------------------------------------
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> "Session":
        """
        Construye una Session a partir de un dict tal y como
        lo devuelve Supabase (ca_sessions).
        """
        if row is None:
            raise ValueError("No se puede construir Session desde None")

        # status viene como texto desde la BD
        status_str = row.get("status") or SessionStatus.PARKED.value
        try:
            status = SessionStatus(status_str)
        except ValueError:
            # Si llega un estado desconocido, lo dejamos como texto bruto
            # pero internamente seguimos usando el Enum para valores conocidos.
            status = SessionStatus.PARKED

        return cls(
            id=str(row["id"]),
            product_id=row["product_id"],
            organization_id=str(row["organization_id"]),
            series_id=str(row["series_id"]) if row.get("series_id") else None,
            sequence_number=row.get("sequence_number"),
            status=status,
            capacity=int(row.get("capacity", 0) or 0),
            pax_registered=int(row.get("pax_registered", 0) or 0),
            activated_at=_parse_dt(row.get("activated_at")),
            expires_at=_parse_dt(row.get("expires_at")),
            finished_at=_parse_dt(row.get("finished_at")),
            created_at=_parse_dt(row.get("created_at")),
            extra={},  # por ahora vacío; se puede rellenar en servicios
        )

    def to_db_update(self) -> Dict[str, Any]:
        """
        Devuelve un dict con los campos que se deberían persistir
        al actualizar la sesión en Supabase.

        Útil para:
        - motores (adjudicación, expiración, rolling)
        - actualización manual de estado
        """
        return {
            "status": self.status.value,
            "capacity": self.capacity,
            "pax_registered": self.pax_registered,
            "activated_at": _serialize_dt(self.activated_at),
            "expires_at": _serialize_dt(self.expires_at),
            "finished_at": _serialize_dt(self.finished_at),
            # No tocamos product_id / organization_id / series_id / sequence_number aquí
        }

    # -----------------------------------------------------
    # PROPIEDADES DE DOMINIO (REGLAS DE NEGOCIO)
    # -----------------------------------------------------
    @property
    def is_active(self) -> bool:
        return self.status == SessionStatus.ACTIVE

    @property
    def is_finished(self) -> bool:
        return self.status == SessionStatus.FINISHED

    @property
    def is_parked(self) -> bool:
        return self.status == SessionStatus.PARKED

    @property
    def is_full(self) -> bool:
        """
        Aforo completo (regla: pax_registered == capacity)
        """
        return self.pax_registered >= self.capacity and self.capacity > 0

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        """
        Indica si la sesión está expirada (según expires_at),
        independientemente de que el motor de expiración la haya marcado
        ya como finished o no.
        """
        if self.expires_at is None:
            return False

        if now is None:
            now = datetime.now(timezone.utc)

        # Normalizamos a aware si viene naive
        exp = _ensure_aware(self.expires_at)
        now = _ensure_aware(now)

        return exp < now

    # -----------------------------------------------------
    # INVARIANTES Y VALIDACIONES
    # -----------------------------------------------------
    def validate_invariants(self) -> None:
        """
        Valida reglas internas de dominio. Lanza ValueError si algo no cuadra.
        Útil para tests y para motores críticos.
        """
        if self.capacity <= 0:
            raise ValueError(f"Session {self.id}: capacity debe ser > 0")

        if self.pax_registered < 0:
            raise ValueError(f"Session {self.id}: pax_registered no puede ser negativo")

        if self.pax_registered > self.capacity:
            raise ValueError(
                f"Session {self.id}: pax_registered ({self.pax_registered}) "
                f"no puede superar capacity ({self.capacity})"
            )

    # -----------------------------------------------------
    # ACCIONES DE DOMINIO (sin efectos de I/O)
    # -----------------------------------------------------
    def with_incremented_pax(self, delta: int = 1) -> "Session":
        """
        Devuelve una nueva Session (copia) con pax_registered incrementado.

        NO toca BD ni logs; eso lo hacen los servicios.
        """
        new_pax = self.pax_registered + delta
        if new_pax < 0:
            raise ValueError("pax_registered no puede ser negativo")

        return Session(
            id=self.id,
            product_id=self.product_id,
            organization_id=self.organization_id,
            series_id=self.series_id,
            sequence_number=self.sequence_number,
            status=self.status,
            capacity=self.capacity,
            pax_registered=new_pax,
            activated_at=self.activated_at,
            expires_at=self.expires_at,
            finished_at=self.finished_at,
            created_at=self.created_at,
            extra=dict(self.extra),
        )

    def mark_as_active(self, activated_at: Optional[datetime] = None,
                       expires_at: Optional[datetime] = None) -> "Session":
        """
        Devuelve una nueva Session marcada como ACTIVE.
        """
        if activated_at is None:
            activated_at = datetime.now(timezone.utc)

        return Session(
            id=self.id,
            product_id=self.product_id,
            organization_id=self.organization_id,
            series_id=self.series_id,
            sequence_number=self.sequence_number,
            status=SessionStatus.ACTIVE,
            capacity=self.capacity,
            pax_registered=self.pax_registered,
            activated_at=_ensure_aware(activated_at),
            expires_at=_ensure_aware(expires_at) if expires_at else self.expires_at,
            finished_at=self.finished_at,
            created_at=self.created_at,
            extra=dict(self.extra),
        )

    def mark_as_finished(self, finished_at: Optional[datetime] = None) -> "Session":
        """
        Devuelve una nueva Session marcada como FINISHED.
        """
        if finished_at is None:
            finished_at = datetime.now(timezone.utc)

        return Session(
            id=self.id,
            product_id=self.product_id,
            organization_id=self.organization_id,
            series_id=self.series_id,
            sequence_number=self.sequence_number,
            status=SessionStatus.FINISHED,
            capacity=self.capacity,
            pax_registered=self.pax_registered,
            activated_at=self.activated_at,
            expires_at=self.expires_at,
            finished_at=_ensure_aware(finished_at),
            created_at=self.created_at,
            extra=dict(self.extra),
        )


# =========================================================
# HELPERS PRIVADOS
# =========================================================

def _parse_dt(value: Any) -> Optional[datetime]:
    """
    Convierte timestamps de Supabase (string o datetime) a datetime.
    Si value es None o cadena vacía, devuelve None.
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    # Supabase suele devolver ISO-8601
    try:
        return datetime.fromisoformat(str(value))
    except Exception:
        return None


def _serialize_dt(value: Optional[datetime]) -> Optional[str]:
    """
    Convierte datetime a ISO-8601 para enviar a Supabase.
    """
    if value is None:
        return None

    value = _ensure_aware(value)
    return value.isoformat()


def _ensure_aware(dt: datetime) -> datetime:
    """
    Asegura que un datetime tenga tzinfo=UTC.
    Si viene naive, se asume UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
