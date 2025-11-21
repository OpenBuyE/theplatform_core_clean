"""
payment_state.py
Máquina de estados de pago para sesiones de Compra Abierta.

NO modifica datos. Solo:
- Lee sesiones (ca_sessions)
- Lee eventos en audit_logs (fintech + adjudicación)
- Devuelve un estado de pago derivado.

Estados principales (por sesión):

- NOT_FUNDED:
    Ningún depósito confirmado por la Fintech.

- PARTIALLY_FUNDED:
    Al menos un depósito confirmado, pero menos que la capacidad.

- FULLY_FUNDED:
    Depósitos confirmados para TODOS los participantes esperados
    (capacity), pero aún sin adjudicar.

- ADJUDICATED_PENDING_SETTLEMENT:
    Sesión adjudicada (motor determinista) y totalmente financiada,
    pero aún sin confirmación de liquidación Fintech.

- SETTLED:
    Fintech ha ejecutado la liquidación completa (pago proveedor + OÜ + DMHG).

- FORCE_MAJEURE_REFUND:
    Caso excepcional: el proveedor no puede entregar el producto y
    se devuelve al adjudicatario SOLO el precio del producto.
"""

from enum import Enum
from typing import Dict, List, Optional

from .supabase_client import supabase
from .session_repository import session_repository


AUDIT_TABLE = "audit_logs"


class PaymentState(str, Enum):
    NOT_FUNDED = "not_funded"
    PARTIALLY_FUNDED = "partially_funded"
    FULLY_FUNDED = "fully_funded"
    ADJUDICATED_PENDING_SETTLEMENT = "adjudicated_pending_settlement"
    SETTLED = "settled"
    FORCE_MAJEURE_REFUND = "force_majeure_refund"


# ---------------------------------------------------------
# Helpers internos para leer eventos de auditoría
# ---------------------------------------------------------
def _get_audit_events_for_session(session_id: str, limit: int = 1000) -> List[Dict]:
    """
    Devuelve todos los eventos de audit_logs asociados a una sesión,
    ordenados por created_at ASC.
    """
    response = (
        supabase
        .table(AUDIT_TABLE)
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", asc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


def _count_deposits_ok(events: List[Dict]) -> int:
    """
    Cuenta eventos fintech_deposit_ok con status = AUTHORIZED.
    """
    count = 0
    for ev in events:
        if ev.get("action") == "fintech_deposit_ok":
            meta = ev.get("metadata") or {}
            if meta.get("status") == "AUTHORIZED":
                count += 1
    return count


def _has_settlement(events: List[Dict]) -> bool:
    """
    ¿Hay liquidación completada por la Fintech?
    """
    for ev in events:
        if ev.get("action") == "fintech_settlement":
            meta = ev.get("metadata") or {}
            if meta.get("status") == "SETTLED":
                return True
    return False


def _has_force_majeure_refund(events: List[Dict]) -> bool:
    """
    ¿Se ha registrado un caso de fuerza mayor con devolución?
    """
    return any(ev.get("action") == "fintech_force_majeure_refund" for ev in events)


def _is_adjudicated(events: List[Dict]) -> bool:
    """
    ¿La sesión ha sido adjudicada por el motor determinista?
    """
    return any(ev.get("action") == "session_adjudicated" for ev in events)


# ---------------------------------------------------------
# API pública del módulo
# ---------------------------------------------------------
def compute_session_payment_state(session_id: str) -> PaymentState:
    """
    Calcula el estado de pago de una sesión a partir de:
    - La sesión (ca_sessions)
    - Eventos de audit_logs relacionados con la Fintech y la adjudicación.
    """

    # 1) Cargar sesión
    session = session_repository.get_session_by_id(session_id)
    if not session:
        # Si no existe, lo tratamos como NOT_FUNDED a efectos prácticos
        return PaymentState.NOT_FUNDED

    capacity = session.get("capacity", 0) or 0

    # 2) Cargar eventos de auditoría
    events = _get_audit_events_for_session(session_id)

    deposits_ok = _count_deposits_ok(events)
    settled = _has_settlement(events)
    fm_refund = _has_force_majeure_refund(events)
    adjudicated = _is_adjudicated(events)

    # 3) Lógica de estados (de más específico a más genérico)

    # Caso excepcional tiene prioridad máxima
    if fm_refund:
        return PaymentState.FORCE_MAJEURE_REFUND

    # Liquidación completada
    if settled:
        return PaymentState.SETTLED

    # Adjudicada + full funded pero todavía sin liquidar
    if adjudicated and capacity > 0 and deposits_ok >= capacity:
        return PaymentState.ADJUDICATED_PENDING_SETTLEMENT

    # Full funded (depósitos confirmados para todo el aforo)
    if capacity > 0 and deposits_ok >= capacity:
        return PaymentState.FULLY_FUNDED

    # Parcialmente financiada
    if deposits_ok > 0:
        return PaymentState.PARTIALLY_FUNDED

    # Ningún depósito OK
    return PaymentState.NOT_FUNDED


def is_session_fully_funded(session_id: str) -> bool:
    """
    ¿Tiene la sesión depósitos confirmados para TODO el aforo?
    (incluye estados avanzados: adjudicada, liquidada, fuerza mayor)
    """
    state = compute_session_payment_state(session_id)
    return state in {
        PaymentState.FULLY_FUNDED,
        PaymentState.ADJUDICATED_PENDING_SETTLEMENT,
        PaymentState.SETTLED,
        PaymentState.FORCE_MAJEURE_REFUND,
    }


def is_session_ready_for_liquidation(session_id: str) -> bool:
    """
    ¿Está la sesión lista para que la Fintech ejecute la liquidación?
    - Esto implica:
      * FULLY_FUNDED
      * y ya adjudicada por el motor determinista.
    """
    state = compute_session_payment_state(session_id)
    return state == PaymentState.ADJUDICATED_PENDING_SETTLEMENT
