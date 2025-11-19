from .supabase_client import supabase_select

def get_sessions():
    """Devuelve todas las sesiones desde Supabase."""
    return supabase_select("sessions")
