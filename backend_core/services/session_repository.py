from .supabase_client import table

# ============================
#   LECTURA DE SESIONES
# ============================

def get_sessions():
    res = table("sessions").select("*").execute()
    return res.data or []

def get_all_sessions():
    res = table("sessions").select("*").order("created_at").execute()
    return res.data or []

def get_active_sessions():
    res = table("sessions").select("*").eq("status", "active").execute()
    return res.data or []

def get_parked_sessions():
    res = table("sessions").select("*").eq("status", "parked").execute()
    return res.data or []

def get_finished_sessions():
    res = table("sessions").select("*").eq("status", "finished").execute()
    return res.data or []

def get_expired_sessions():
    res = (
        table("sessions")
        .select("*")
        .eq("status", "expired")
        .execute()
    )
    return res.data or []

def get_session_by_id(session_id: str):
    res = table("sessions").select("*").eq("id", session_id).execute()
    if res.data:
        return res.data[0]
    return None

# ============================
#   PARTICIPANTES
# ============================

def get_participants_for_session(session_id: str):
    res = (
        table("participants")
        .select("*")
        .eq("session_id", session_id)
        .execute()
    )
    return res.data or []

def get_participants_sorted(session_id: str):
    res = (
        table("participants")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )
    return res.data or []

# ============================
#   OPERACIONES DE SESIÓN
# ============================

def activate_session(session_id: str):
    return (
        table("sessions")
        .update({"status": "active"})
        .eq("id", session_id)
        .execute()
    )

def mark_session_finished(session_id: str):
    return (
        table("sessions")
        .update({"status": "finished"})
        .eq("id", session_id)
        .execute()
    )

def finish_session(session_id: str):
    return mark_session_finished(session_id)

def create_session(session_data: dict):
    return table("sessions").insert(session_data).execute()

# ============================
#   SERIES DE SESIONES
# ============================

def get_session_series(series_id: str):
    res = (
        table("session_series")
        .select("*")
        .eq("id", series_id)
        .execute()
    )
    if res.data:
        return res.data[0]
    return None

def get_sessions_by_series(series_id: str):
    res = (
        table("sessions")
        .select("*")
        .eq("series_id", series_id)
        .order("created_at")
        .execute()
    )
    return res.data or []

def get_next_session_in_series(series_id: str):
    res = (
        table("sessions")
        .select("*")
        .eq("series_id", series_id)
        .eq("status", "scheduled")
        .order("created_at")
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]
    return None
