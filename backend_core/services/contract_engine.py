# backend_core/services/contract_engine.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from backend_core.services import supabase_client
from backend_core.services.audit_repository import AuditRepository
from backend_core.services.payment_session_repository import (
    create_payment_session,
    get_payment_session_by_session_id,
)
from backend_core.services.contract_session_repository import (
    create_contract_session,
    get_contract_by_session_id,
    mark_deposits_completed,
    mark_settlement_requested,
    mark_provider_paid,
    mark_delivered,
    mark_closed,
    mark_force_majeure,
    mark_refunded,
)
from backend_core.models.contract_session import ContractStatus
from backend_core.models.payment_state import PaymentStatus

audit_repo = AuditRepository()
