# backend_core/dashboard/views/admin_seeds.py

import streamlit as st
from datetime import datetime

from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event

SEEDS_TABLE = "ca_adjudication_seeds"


def _get_seed_for_session(session_id: str):
    resp = (
        table(SEEDS_TABLE)
        .select("*")
        .eq("session_id", session_id)
        .execute()
    )
    rows = resp.data or []
    return rows[0] if rows else None


def _set_seed_for_session(session_id: str, public_seed: str):
    existing = _get_seed_for_session(session_id)

    now_iso = datetime.utcnow().isoformat()

    if existing:
        # update existente
        resp = (
            table(SEEDS_TABLE)
            .update({"public_seed": public_seed, "created_at": now_iso})
            .eq("id", existing["id"])
            .execute()
        )
        row = resp.data[0]
    else:
        # insertar nueva
        resp = (
            table(SEEDS_TABLE)
            .insert(
                {
                    "session_id": session_id,
                    "public_seed": public_seed,
                    "created_at": now_iso,
                }
            )
            .execute()
        )
        row = resp.data[0]

    log_event(
        "seed_set_for_session",
        session_id=session_id,
        user_id=None,
        metadata={"public_seed": public_seed},
    )

    return row


def render_admin_seeds():
    st.header("🔑 Admin Seeds (Semilla Pública de Adjudicación)")

    st.write(
        "Aquí puedes consultar y fijar la **public_seed** asociada a cada sesión. "
        "Forma parte del mecanismo determinista auditable."
    )

    st.markdown("---")

    # ===========================
    # BLOQUE: CONSULTAR / EDITAR
    # ===========================
    st.subheader("Consultar / Editar seed de una sesión")

    session_id = st.text_input("Session ID:", placeholder="UUID de la sesión")

    if session_id:
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Ver seed actual"):
                seed = _get_seed_for_session(session_id)
                if seed:
                    st.success(f"Seed actual: `{seed['public_seed']}`")
                    st.json(seed)
                else:
                    st.info("Esta sesión no tiene seed registrada todavía.")

        with col2:
            new_seed = st.text_input("Nueva public_seed (texto libre):", key="new_seed_input")

            if st.button("Guardar nueva seed"):
                if not new_seed:
                    st.error("Debes indicar una seed.")
                else:
                    row = _set_seed_for_session(session_id, new_seed)
                    st.success("Seed guardada correctamente.")
                    st.json(row)

    st.markdown("---")

    # ===========================
    # BLOQUE: LISTADO SIMPLE
    # ===========================
    st.subheader("Listado rápido de seeds registradas")

    # Listado simple sin order/limit para evitar problemas con el wrapper
    try:
        resp = table(SEEDS_TABLE).select("*").execute()
        seeds = resp.data or []
        if not seeds:
            st.info("Todavía no hay seeds registradas en ca_adjudication_seeds.")
        else:
            # Mostramos solo las primeras 50 para no saturar
            for s in seeds[:50]:
                st.write(
                    f"- Session: `{s.get('session_id')}` — "
                    f"Seed: `{s.get('public_seed')}` — "
                    f"Created_at: {s.get('created_at')}"
                )
    except Exception as e:
        st.error(f"Error cargando seeds: {e}")
