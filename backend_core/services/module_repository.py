# backend_core/services/module_repository.py

from __future__ import annotations

from typing import List, Dict, Optional
from uuid import uuid4

from backend_core.services import supabase_client
from backend_core.services.audit_repository import log_event

MODULES_TABLE = "ca_modules"


# ============================================================
# CREATE MODULE
# ============================================================

def create_module(module_code: str, config: Dict = None) -> Dict:
    row = {
        "id": str(uuid4()),
        "module_code": module_code,
        "config": config or {},
        "has_award": False,
        "module_status": "active",
    }

    resp = supabase_client.table(MODULES_TABLE).insert(row).execute()
    log_event("module_created", metadata=row)

    return resp.data[0]


# ============================================================
# LIST ALL MODULES
# ============================================================

def list_all_modules() -> List[Dict]:
    resp = supabase_client.table(MODULES_TABLE).select("*").order("module_code").execute()
    return resp.data or []


# ============================================================
# GET MODULE FOR SESSION
# ============================================================

def get_module_for_session(session_id: str) -> Optional[Dict]:
    resp = (
        supabase_client.table(MODULES_TABLE)
        .select("*")
        .eq("session_id", session_id)
        .single()
        .execute()
    )
    return resp.data


# ============================================================
# ASSIGN MODULE TO SESSION
# ============================================================

def assign_module(session_id: str, module_id: str):
    resp = (
        supabase_client.table(MODULES_TABLE)
        .update({"session_id": session_id})
        .eq("id", module_id)
        .execute()
    )

    log_event("module_assigned", session_id=session_id, metadata={"module_id": module_id})
    return resp.data


# ============================================================
# MARK MODULE AS AWARDED
# ============================================================

def mark_module_awarded(module_id: str):
    supabase_client.table(MODULES_TABLE).update({"has_award": True}).eq("id", module_id).execute()
    log_event("module_marked_awarded", metadata={"module_id": module_id})
