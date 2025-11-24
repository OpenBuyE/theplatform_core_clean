# backend_core/services/module_repository.py

from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime

from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event

MODULES_TABLE = "ca_modules"
BATCHES_TABLE = "ca_module_batches"


# ============================================================
# CREATE MODULE
# ============================================================

def create_module(
    product_id: str,
    module_code: str,
    organization_id: str,
    batch_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Crea un módulo base en ca_modules.
    """

    now = datetime.utcnow().isoformat()

    resp = (
        table(MODULES_TABLE)
        .insert(
            {
                "product_id": product_id,
                "module_code": module_code,
                "organization_id": organization_id,
                "batch_id": batch_id,
                "module_status": "pending",  # pending / active / cancelled / archived / no_award
                "has_award": None,
                "created_at": now,
            }
        )
        .execute()
    )

    module = resp.data[0]

    log_event(
        "module_created",
        session_id=None,
        metadata={
            "module_id": module["id"],
            "module_code": module_code,
            "product_id": product_id,
            "organization_id": organization_id,
            "batch_id": batch_id,
        },
    )

    return module


# ============================================================
# GET MODULE BY ID
# ============================================================

def get_module_by_id(module_id: str) -> Optional[Dict[str, Any]]:
    resp = (
        table(MODULES_TABLE)
        .select("*")
        .eq("id", module_id)
        .single()
        .execute()
    )
    return resp.data


# ============================================================
# LIST MODULES BY PRODUCT
# ============================================================

def get_modules_by_product(product_id: str) -> List[Dict[str, Any]]:
    resp = (
        table(MODULES_TABLE)
        .select("*")
        .eq("product_id", product_id)
        .order("created_at")
        .execute()
    )
    return resp.data or []


# ============================================================
# LIST MODULES BY BATCH
# ============================================================

def get_modules_by_batch(batch_id: str) -> List[Dict[str, Any]]:
    resp = (
        table(MODULES_TABLE)
        .select("*")
        .eq("batch_id", batch_id)
        .order("created_at")
        .execute()
    )
    return resp.data or []


# ============================================================
# LIST ALL MODULES
# ============================================================

def list_all_modules() -> List[Dict[str, Any]]:
    resp = (
        table(MODULES_TABLE)
        .select("*")
        .order("created_at")
        .execute()
    )
    return resp.data or []


# ============================================================
# LIST ARCHIVED MODULES
# ============================================================

def list_archived_modules() -> List[Dict[str, Any]]:
    resp = (
        table(MODULES_TABLE)
        .select("*")
        .eq("module_status", "archived")
        .order("archived_at", desc=True)
        .execute()
    )
    return resp.data or []


# ============================================================
# LIST CANCELLED MODULES
# ============================================================

def list_cancelled_modules() -> List[Dict[str, Any]]:
    resp = (
        table(MODULES_TABLE)
        .select("*")
        .eq("module_status", "cancelled")
        .order("created_at")
        .execute()
    )
    return resp.data or []


# ============================================================
# LIST MODULES WITH NO AWARD
# ============================================================

def list_no_award_modules() -> List[Dict[str, Any]]:
    resp = (
        table(MODULES_TABLE)
        .select("*")
        .eq("module_status", "no_award")
        .order("created_at")
        .execute()
    )
    return resp.data or []


# ============================================================
# UPDATE MODULE STATUS
# ============================================================

def update_module_status(module_id: str, status: str) -> Optional[Dict[str, Any]]:
    now = datetime.utcnow().isoformat()

    update_data = {
        "module_status": status,
        "updated_at": now,
    }

    if status == "archived":
        update_data["archived_at"] = now

    resp = (
        table(MODULES_TABLE)
        .update(update_data)
        .eq("id", module_id)
        .execute()
    )

    data = resp.data[0] if resp.data else None

    log_event(
        "module_status_updated",
        session_id=None,
        metadata={
            "module_id": module_id,
            "new_status": status,
        },
    )

    return data


# ============================================================
# ASSIGN MODULE TO SESSION
# ============================================================

def assign_module_to_session(module_id: str, session_id: str):
    """
    Vincula un módulo a una sesión concreta.
    """

    resp = (
        table(MODULES_TABLE)
        .update({"session_id": session_id})
        .eq("id", module_id)
        .execute()
    )

    log_event(
        "module_assigned_session",
        session_id=session_id,
        metadata={
            "module_id": module_id,
            "session_id": session_id,
        },
    )

    return resp.data[0] if resp.data else None


# ============================================================
# MARK MODULE AS AWARDED
# ============================================================

def mark_module_awarded(module_id: str):
    resp = (
        table(MODULES_TABLE)
        .update(
            {
                "has_award": True,
                "module_status": "finished",
                "awarded_at": datetime.utcnow().isoformat(),
            }
        )
        .eq("id", module_id)
        .execute()
    )

    log_event(
        "module_awarded",
        session_id=None,
        metadata={"module_id": module_id},
    )

    return resp.data[0] if resp.data else None

