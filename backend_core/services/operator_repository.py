# backend_core/services/operator_repository.py

from __future__ import annotations

from typing import Optional, Dict, Any, List
from datetime import datetime

from backend_core.services import supabase_client
from backend_core.models.operator import (
    Operator,
    OperatorKycStatus,
    OperatorKycLog,
)


OPERATORS_TABLE = "ca_operators"
OPERATORS_KYC_LOGS_TABLE = "ca_operator_kyc_logs"


# ------------------------------------------------------
# CRUD básico de operadores
# ------------------------------------------------------

def create_operator(
    organization_id: str,
    name: str,
    country: Optional[str] = None,
    legal_person_type: Optional[str] = None,
) -> Operator:
    payload = {
        "organization_id": organization_id,
        "name": name,
        "country": country,
        "legal_person_type": legal_person_type,
        "kyc_status": OperatorKycStatus.PENDING.value,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    resp = supabase_client.table(OPERATORS_TABLE).insert(payload).execute()
    row = resp.data[0]
    return Operator(**row)


def get_operator_by_id(operator_id: str) -> Optional[Operator]:
    resp = (
        supabase_client.table(OPERATORS_TABLE)
        .select("*")
        .eq("id", operator_id)
        .single()
        .execute()
    )
    if not resp.data:
        return None
    return Operator(**resp.data)


def get_operator_by_organization_id(organization_id: str) -> Optional[Operator]:
    resp = (
        supabase_client.table(OPERATORS_TABLE)
        .select("*")
        .eq("organization_id", organization_id)
        .single()
        .execute()
    )
    if not resp.data:
        return None
    return Operator(**resp.data)


def list_operators() -> List[Operator]:
    resp = (
        supabase_client.table(OPERATORS_TABLE)
        .select("*")
        .order("created_at")
        .execute()
    )
    rows = resp.data or []
    return [Operator(**row) for row in rows]


def update_operator_mangopay_ids(
    operator_id: str,
    mangopay_legal_user_id: Optional[str] = None,
    mangopay_wallet_id: Optional[str] = None,
) -> Optional[Operator]:
    updates: Dict[str, Any] = {
        "updated_at": datetime.utcnow().isoformat(),
    }
    if mangopay_legal_user_id is not None:
        updates["mangopay_legal_user_id"] = mangopay_legal_user_id
    if mangopay_wallet_id is not None:
        updates["mangopay_wallet_id"] = mangopay_wallet_id

    resp = (
        supabase_client.table(OPERATORS_TABLE)
        .update(updates)
        .eq("id", operator_id)
        .execute()
    )

    if not resp.data:
        return None
    return Operator(**resp.data[0])


def update_operator_kyc_status(
    operator_id: str,
    new_status: OperatorKycStatus,
    kyc_level: Optional[str] = None,
) -> Optional[Operator]:
    updates: Dict[str, Any] = {
        "kyc_status": new_status.value,
        "updated_at": datetime.utcnow().isoformat(),
    }
    if kyc_level is not None:
        updates["kyc_level"] = kyc_level

    resp = (
        supabase_client.table(OPERATORS_TABLE)
        .update(updates)
        .eq("id", operator_id)
        .execute()
    )
    if not resp.data:
        return None
    return Operator(**resp.data[0])


# ------------------------------------------------------
# KYC Logs
# ------------------------------------------------------

def log_operator_kyc_event(
    operator_id: str,
    event_type: str,
    mangopay_kyc_id: Optional[str],
    status: Optional[str],
    payload: Dict[str, Any],
) -> OperatorKycLog:
    row_payload = {
        "operator_id": operator_id,
        "event_type": event_type,
        "mangopay_kyc_id": mangopay_kyc_id,
        "status": status,
        "payload": payload,
        "created_at": datetime.utcnow().isoformat(),
    }

    resp = (
        supabase_client.table(OPERATORS_KYC_LOGS_TABLE)
        .insert(row_payload)
        .execute()
    )
    return OperatorKycLog(**resp.data[0])


def list_operator_kyc_logs(operator_id: str) -> List[OperatorKycLog]:
    resp = (
        supabase_client.table(OPERATORS_KYC_LOGS_TABLE)
        .select("*")
        .eq("operator_id", operator_id)
        .order("created_at", desc=True)
        .execute()
    )
    rows = resp.data or []
    return [OperatorKycLog(**row) for row in rows]
