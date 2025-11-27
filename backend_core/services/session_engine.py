# backend_core/services/session_engine.py

from backend_core.services.supabase_client import table
from datetime import datetime

def advance_series(series_id: str):
    return table("session_series").update({
        "advanced_at": datetime.utcnow().isoformat()
    }).eq("id", series_id).execute()
