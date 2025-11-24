# backend_core/services/kpi_repository.py

from backend_core.services.supabase_client import table


def kpi_sessions_active():
    resp = (
        table("ca_sessions")
        .select("id")
        .eq("status", "active")
        .execute()
    )
    return len(resp.data or [])


def kpi_sessions_finished():
    resp = (
        table("ca_sessions")
        .select("id")
        .eq("status", "finished")
        .execute()
    )
    return len(resp.data or [])


def kpi_wallet_deposit_ok():
    resp = (
        table("ca_audit_logs")
        .select("id")
        .eq("action", "wallet_deposit_ok")
        .execute()
    )
    return len(resp.data or [])


def kpi_wallet_settlement_completed():
    resp = (
        table("ca_audit_logs")
        .select("id")
        .eq("action", "wallet_settlement_completed")
        .execute()
    )
    return len(resp.data or [])


def kpi_wallet_force_majeure():
    resp = (
        table("ca_audit_logs")
        .select("id")
        .eq("action", "wallet_force_majeure_refund")
        .execute()
    )
    return len(resp.data or [])


def kpi_sessions_by_module():
    resp = (
        table("ca_session_modules")
        .select("module_id")
        .execute()
    )
    rows = resp.data or []
    stats = {}

    for r in rows:
        m = r.get("module_id")
        stats[m] = stats.get(m, 0) + 1

    return stats
