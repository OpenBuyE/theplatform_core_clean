def kpi_audit_events_by_day():
    resp = (
        table("ca_audit_logs")
        .select("created_at")
        .execute()
    )
    rows = resp.data or []
    stats = {}

    for r in rows:
        day = r["created_at"].split("T")[0]  # YYYY-MM-DD
        stats[day] = stats.get(day, 0) + 1

    return stats


def kpi_sessions_status_distribution():
    resp = (
        table("ca_sessions")
        .select("status")
        .execute()
    )
    rows = resp.data or []
    stats = {}

    for r in rows:
        status = r["status"]
        stats[status] = stats.get(status, 0) + 1

    return stats
