import streamlit as st

from backend_core.services.session_repository import session_repository
from backend_core.services.session_engine import session_engine
from backend_core.services.audit_repository import log_event
from backend_core.services.supabase_client import supabase

import uuid
from datetime import datetime, timedelta


# ==========================================================
#  CREAR NUEVA SERIE (si el usuario desea)
# ==========================================================
def _create_series(organization_id: str, product_id: str) -> str:
    new_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    supabase.table("ca_session_series").insert({
        "id": new_id,
        "organization_id": organization_id,
        "product_id": product_id,
        "created_at": now
    }).execute()

    return new_id


# ==========================================================
#  CREAR SESIÓN PARKED
# ==========================================================
def _create_parked_session(series_id: str, product_id: str, organization_id: str, capacity: int):
    session_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    supabase.table("ca_sessions").insert({
        "id": session_id,
        "product_id": product_id,
        "series_id": series_id,
        "organization_id": organization_id,
        "sequence_number": 1,          # La primera sesión de la serie
        "status": "parked",
        "capacity": capacity,
        "pax_registered": 0,
        "created_at": now
    }).execute()

    log_event(
        action="session_created_parked",
        session_id=session_id,
        metadata={"product_id": product_id, "series_id": series_id}
    )

    return session_id


# ==========================================================
#  PANEL DE SESIONES PARKED
# ==========================================================
def render_park_sessions():
    st.header("🟦 Sesiones Parked")

    # Cargar sesiones parked
    parked = session_repository.get_sessions(status="parked")

    # ======================================================
    # FORMULARIO: CREAR SESIÓN PARKED
    # ======================================================
    st.subheader("➕ Crear Nueva Sesión Parked")

    with st.form("form_create_parked"):
        col1, col2 = st.columns(2)

        product_id = col1.text_input("Product ID")
        organization_id = col2.text_input("Organization ID")

        with col1:
            create_series = st.checkbox("Crear serie nueva", value=True)

        with col2:
            series_id_input = st.text_input("Series ID (si NO se crea nueva)")

        capacity = st.number_input("Capacidad", min_value=1, value=10, step=1)

        submitted = st.form_submit_button("Crear Sesión Parked")

    if submitted:
        if not product_id or not organization_id:
            st.error("Debes introducir Product ID y Organization ID.")
        else:
            if create_series:
                series_id = _create_series(organization_id, product_id)
            else:
                if not series_id_input:
                    st.error("Introduce un Series ID o marca 'Crear serie nueva'.")
                    return
                series_id = series_id_input.strip()

            new_session_id = _create_parked_session(
                series_id=series_id,
                product_id=product_id,
                organization_id=organization_id,
                capacity=capacity
            )

            st.success(f"Sesión creada correctamente: {new_session_id}")
            st.rerun()

    # ======================================================
    # LISTADO DE SESIONES PARKED
    # ======================================================
    st.subheader("📋 Lista de Sesiones Parked")

    if not parked:
        st.info("No hay sesiones parked.")
        return

    for s in parked:
        with st.expander(f"🟦 Sesión {s['id']} — Prod:{s['product_id']}"):
            st.write("**Series ID:**", s["series_id"])
            st.write("**Capacidad:**", s["capacity"])
            st.write("**Pax registrados:**", s["pax_registered"])
            st.write("**Creada en:**", s["created_at"])

            # Botón activar sesión
            if st.button(f"Activar {s['id']}", key=f"activate_{s['id']}"):
                activated = session_repository.activate_session(s["id"])
                if activated:
                    log_event(
                        action="parked_session_activated",
                        session_id=s["id"],
                        metadata={"activated_id": activated["id"]}
                    )
                    st.success(f"Sesión activada: {activated['id']}")
                    st.rerun()
                else:
                    st.error("No se pudo activar la sesión.")

