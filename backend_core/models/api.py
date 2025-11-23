"""
backend_core/models/api.py
Modelos Pydantic (DTOs) para la API pública / interna.

Objetivo:
- Separar claramente el dominio (tablas Supabase, lógica interna)
  de los modelos de entrada/salida de la API (FastAPI, webhooks, etc.).
- Facilitar validación estricta y documentación automática (OpenAPI).

IMPORTANTE:
- Este archivo NO cambia aún la lógica de negocio.
- Más adelante iremos actualizando los endpoints FastAPI para usar estos modelos.
"""

from datetime import datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field


# ============================================================
#  SESIONES (DTOs de API)
# ============================================================

class SessionBase(BaseModel):
    """
    Campos comunes de una sesión expuesta por API.
    Equivalente a ca_sessions, pero en modo lectura/escritura.
    """

    product_id: str = Field(..., description="Identificador lógico del producto")
    organization_id: str = Field(..., description="UUID de la organización propietaria")
    series_id: Optional[str] = Field(
        None,
        description="UUID de la serie a la que pertenece la sesión (si aplica)",
    )
    sequence_number: Optional[int] = Field(
        None,
        description="Orden dentro de la serie (1,2,3...)",
        ge=1,
    )
    status: Literal["parked", "active", "finished"] = Field(
        "parked",
        description="Estado de la sesión",
    )
    capacity: int = Field(
        ...,
        description="Aforo total obligatorio de la sesión (pax)",
        gt=0,
    )
    pax_registered: int = Field(
        0,
        description="Número de participantes registrados",
        ge=0,
    )


class SessionCreateParked(BaseModel):
    """
    Payload para crear una nueva sesión parked desde la API/panel.
    Ejemplo de uso:
    - Botón "Crear Sesión Parked" en el panel
    - Endpoint REST /sessions/parked
    """

    product_id: str = Field(..., description="Identificador del producto")
    organization_id: str = Field(..., description="UUID de la organización")
    capacity: int = Field(..., gt=0, description="Aforo (pax) de la sesión")
    series_id: Optional[str] = Field(
        None,
        description="Serie a la que se engancha (si existe). Si es None, se creará serie nueva.",
    )


class SessionRead(SessionBase):
    """
    Modelo de lectura de sesión (lo que devolvemos desde la API).
    Incluye metadatos de tiempo.
    """

    id: str = Field(..., description="UUID de la sesión")
    activated_at: Optional[datetime] = Field(None, description="Momento de activación")
    expires_at: Optional[datetime] = Field(None, description="Fecha/hora de expiración")
    finished_at: Optional[datetime] = Field(None, description="Fecha/hora de cierre")
    created_at: datetime = Field(..., description="Fecha de creación")


class SessionActivateRequest(BaseModel):
    """
    Payload para activar una sesión parked.
    """

    session_id: str = Field(..., description="UUID de la sesión a activar")
    expires_at: Optional[datetime] = Field(
        None,
        description="Fecha/hora de expiración manual (opcional). Si no se pasa, 5 días desde ahora.",
    )


# ============================================================
#  PARTICIPANTES (DTOs de API)
# ============================================================

class ParticipantBase(BaseModel):
    """
    Campos comunes de un participante.
    """

    session_id: str = Field(..., description="UUID de la sesión")
    user_id: str = Field(..., description="Identificador lógico del usuario")
    organization_id: Optional[str] = Field(
        None,
        description="UUID de la organización (si aplica)",
    )
    amount: float = Field(
        ...,
        ge=0,
        description="Importe total aportado por este participante (precio proporcional)",
    )
    quantity: int = Field(
        1,
        ge=1,
        description="Número de unidades que representa esta participación (normalmente 1)",
    )
    price: float = Field(
        ...,
        ge=0,
        description="Precio unitario (importe por unidad)",
    )


class ParticipantCreate(ParticipantBase):
    """
    Payload estándar para crear un participante real vía API.
    (No test, sino usuario real que entra en la sesión).
    """
    pass


class ParticipantRead(ParticipantBase):
    """
    Modelo de lectura de participante.
    """

    id: str = Field(..., description="UUID del participante")
    is_awarded: bool = Field(False, description="Si ha sido adjudicatario")
    awarded_at: Optional[datetime] = Field(
        None,
        description="Fecha/hora en la que fue marcado como adjudicatario",
    )
    created_at: datetime = Field(..., description="Fecha/hora de creación del registro")


class AdjudicationResult(BaseModel):
    """
    Resumen de una adjudicación.

    Puede ser devuelto por:
    - Endpoints internos de test
    - API pública de consulta de resultado
    """

    session: SessionRead
    awarded_participant: ParticipantRead
    participants: List[ParticipantRead]


# ============================================================
#  FINTECH / WALLET DTOs (para unificar con fintech_routes)
# ============================================================

class FintechDepositNotification(BaseModel):
    """
    Notificación de que un depósito (pago del participante)
    ha sido AUTORIZADO y bloqueado en la Fintech.
    Coincide conceptualmente con fintech_routes.DepositNotification.
    """

    session_id: str
    participant_id: str
    amount: float
    currency: str = "EUR"
    fintech_tx_id: str
    status: str  # ejemplo: "AUTHORIZED", "FAILED", ...


class FintechSettlementNotification(BaseModel):
    """
    Notificación de que la Fintech ha ejecutado la liquidación:
    - Pago al proveedor
    - Comisiones / gastos de gestión
    """

    session_id: str
    adjudicatario_id: str
    fintech_batch_id: str
    status: str  # ejemplo: "SETTLED", "FAILED", ...


class FintechForceMajeureRefund(BaseModel):
    """
    Caso excepcional de fuerza mayor:
    - No se puede entregar el producto.
    - La Fintech devuelve al adjudicatario SOLO el precio del producto.
    """

    session_id: str
    adjudicatario_id: str
    product_amount: float
    currency: str = "EUR"
    fintech_refund_tx_id: Optional[str] = None
    reason: Optional[str] = None


# ============================================================
#  RESPUESTAS GENÉRICAS DE API
# ============================================================

class ApiStatus(BaseModel):
    """
    Respuesta mínima para endpoints simples:
    { "status": "ok", "message": "..." }
    """

    status: Literal["ok", "error"] = "ok"
    message: str


class ApiError(BaseModel):
    """
    Respuesta de error estructurada.
    No es obligatorio usarlo en todos los endpoints, pero deja
    sentada una convención clara.
    """

    status: Literal["error"] = "error"
    message: str
    code: Optional[str] = None
    details: Optional[dict] = None
