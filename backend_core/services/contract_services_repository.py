# backend_core/services/contract_session_repository.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from backend_core.services import supabase_client
from backend_core.models.contract_session import (
    ContractSession,
    ContractStatus,
)


# ----------------------------------------
# CREACIÓN
# ----------------------------------------

def create_contract_session(
    session_id: str,
    payment_session_id: Optional[str],
    adjudicatario_user_id: str,
    organization_id: str,
    provider_id: Optional[str],
    product_id: Optional[str],
) -> ContractSession:
    """
    Crea un expediente contractual desde cero.
    Debe ser llamado una única vez, cuando el adjudicator_engine
    produce un adjudicatario.
    """

    now = datetime.utcnow().isoformat()

    payload = {
        "session_id": session_id,
        "payment_session_id": payment_session_id,
        "adjudicatario_user_id": adjudicatario_user_id,
        "organization_id": organization_id,
        "provider_id": provider_id,
        "product_id": product_id,
        "status": ContractStatus.CREATED,
        "created_at": now,
        "updated_at": now,
        "awarded_at": now,
        "metadata": {},
        "delivery_metadata": {},
    }

    resp = supabase_client.table("ca_contract_sessions").insert(payload).execute()
    row = resp.data[0]

    return ContractSession(**row)


# ----------------------------------------
# LECTURA
# ----------------------------------------

def get_contract_by_session_id(session_id: str) -> Optional[ContractSession]:
    """
    Obtiene el expediente contractual a partir de la sesión.
    """
    resp = (
        supabase_client.table("ca_contract_sessions")
        .select("*")
        .eq("session_id", session_id)
        .single()
        .execute()
    )

    if not resp.data:
        return None

    return ContractSession(**resp.data)


def get_contract_by_id(contract_id: str) -> Optional[ContractSession]:
    """
    Obtiene un contrato por su id (UUID).
    """
    resp = (
        supabase_client.table("ca_contract_sessions")
        .select("*")
        .eq("id", contract_id)
        .single()
        .execute()
    )

    if not resp.data:
        return None

    return ContractSession(**resp.data)


# ----------------------------------------
# ACTUALIZACIÓN GENÉRICA
# ----------------------------------------

def save_contract_session(contract: ContractSession) -> None:
    """
    Persiste cualquier cambio del contrato.
    Se sincroniza directamente con la BBDD.
    """
    supabase_client.table("ca_contract_sessions").update(
        {
            "status": contract.status,
            "payment_session_id": contract.payment_session_id,
            "provider_id": contract.provider_id,
            "product_id": contract.product_id,

            "awarded_at": contract.awarded_at,
            "deposits_completed_at": contract.deposits_completed_at,
            "settlement_requested_at": contract.settlement_requested_at,
            "provider_paid_at": contract.provider_paid_at,
            "delivered_at": contract.delivered_at,
            "closed_at": contract.closed_at,
            "force_majeure_at": contract.force_majeure_at,
            "refunded_at": contract.refunded_at,

            "delivery_method": contract.delivery_method,
            "delivery_location": contract.delivery_location,
            "delivery_metadata": contract.delivery_metadata,

            "metadata": contract.metadata,
            "updated_at": datetime.utcnow().isoformat(),
        }
    ).eq("id", contract.id).execute()


# ----------------------------------------
# HELPERS DE TRANSICIÓN CONTRACTUAL
# ----------------------------------------

def update_contract_status(
    contract: ContractSession,
    new_status: str,
    timestamp_field: Optional[str] = None,
) -> ContractSession:
    """
    Actualiza el estado contractual y asigna timestamp si corresponde.
    EJEMPLO:
        update_contract_status(contract, ContractStatus.GROUP_FUNDED, "deposits_completed_at")
    """

    contract.status = new_status

    if timestamp_field:
        now = datetime.utcnow()
        setattr(contract, timestamp_field, now)

    save_contract_session(contract)
    return contract


# ----------------------------------------
# TRIGGERS DEL CICLO CONTRACTUAL COMPLETO
# ----------------------------------------

def mark_deposits_completed(contract: ContractSession) -> ContractSession:
    return update_contract_status(
        contract,
        ContractStatus.GROUP_FUNDED,
        "deposits_completed_at",
    )


def mark_settlement_requested(contract: ContractSession) -> ContractSession:
    return update_contract_status(
        contract,
        ContractStatus.WAITING_SETTLEMENT,
        "settlement_requested_at",
    )


def mark_provider_paid(contract: ContractSession) -> ContractSession:
    return update_contract_status(
        contract,
        ContractStatus.PROVIDER_PAID,
        "provider_paid_at",
    )


def mark_delivered(contract: ContractSession) -> ContractSession:
    return update_contract_status(
        contract,
        ContractStatus.DELIVERED,
        "delivered_at",
    )


def mark_closed(contract: ContractSession) -> ContractSession:
    return update_contract_status(
        contract,
        ContractStatus.CLOSED,
        "closed_at",
    )


def mark_force_majeure(contract: ContractSession) -> ContractSession:
    return update_contract_status(
        contract,
        ContractStatus.FORCE_MAJEURE,
        "force_majeure_at",
    )


def mark_refunded(contract: ContractSession) -> ContractSession:
    return update_contract_status(
        contract,
        ContractStatus.REFUNDED,
        "refunded_at",
    )
