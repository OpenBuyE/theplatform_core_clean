import streamlit as st
from backend_core.services.supabase_client import client

# ---------------------------
# Obtener sesiones "parked"
# ---------------------------
def get_sessions():
    resp = client.table("sessions").select("*").eq("status", "parked").execute()
    return resp.data or []

# ---------------------------
# Obtener sesiones activas
# ---------------------------
def get_active_sessions():
    resp = client.table("sessions").select("*").in_("status", ["open", "running"]).execute()
    return resp.data or []

# ---------------------------
# Obtener chains
# ---------------------------
def get_chains():
    resp = client.table("sessions").select("*").neq("chain_group_id", None).execute()
    return resp.data or []

