# backend_core/services/wallet_events.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any


# ======================================================
# EVENTOS PRINCIPALES DE WALLET / FINTECH
# ======================================================

@dataclass
class DepositAuthorizedEvent:
    """
    Evento cuando la Fintech confirma un depósito de un participante.
    """
    session_id: str
    user_id: str
    amount: float
    fintech_operation_id: str
    raw_payload: Dict[str, Any]


@dataclass
class SettlementExecutedEvent:
    """
    Evento cuando la Fintech ejecuta el settlement al proveedor.
    """
    session_id: str
    provider_id: str
    amount: float
    fintech_operation_id: str
    raw_payload: Dict[str, Any]


@dataclass
class ForceMajeureRefundEvent:
    """
    Evento cuando la Fintech ejecuta un reembolso por fuerza mayor.
    """
    session_id: str
    adjudicatario_user_id: str
    amount_refunded: float
    fintech_operation_id: str
    raw_payload: Dict[str, Any]
