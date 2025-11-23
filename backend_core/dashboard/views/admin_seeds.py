# backend_core/dashboard/views/admin_seeds.py

import streamlit as st

from backend_core.services import supabase_client
from backend_core.services.audit_repository import AuditRepository

audit = AuditRepository()


def render_admin_seeds():
    st.title("Admin Seeds")
    st.write("Gestionar ca_adjudication_seeds (semillas públicas de adjudicación).")

    # Listar seeds existentes
    resp = (
        supabase_client.table("ca_adjudication_seeds")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    seeds = resp.data or []

    st.subheader("Semillas existentes")
    if seeds:
        st.json(seeds)
    else:
        st.info("No hay semillas registradas.")

    st.subheader("Crear / Actualizar semilla para sesión")

    with st.form("seed_form"):
        session_id = st.text_input("Session ID")
        public_seed = st.text_input("Public Seed")
        submitted = st.form_submit_button("Guardar semilla")

        if submitted:
            if not session_id or not public_seed:
                st.error("Session ID y Public Seed son obligatorios.")
            else:
                # upsert manual
                existing = (
                    supabase_client.table("ca_adjudication_seeds")
                    .select("*")
                    .eq("session_id", session_id)
                    .single()
                    .execute()
                )

                if existing.data:
                    supabase_client.table("ca_adjudication_seeds").update(
                        {"public_seed": public_seed}
                    ).eq("session_id", session_id).execute()
                    action = "SEED_UPDATED"
                else:
                    supabase_client.table("ca_adjudication_seeds").insert(
                        {
                            "session_id": session_id,
                            "public_seed": public_seed,
                        }
                    ).execute()
                    action = "SEED_CREATED"

                audit.log(
                    action=action,
                    session_id=session_id,
                    user_id=None,
                    metadata={"public_seed": public_seed},
                )
                st.success(f"Semilla guardada ({action}).")
                st.experimental_rerun()
