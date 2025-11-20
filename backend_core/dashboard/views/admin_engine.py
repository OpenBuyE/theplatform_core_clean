"""
admin_engine.py
Vista de administración del motor determinista y de expiración.

Permite:
- Ejecutar el motor de expiración manualmente
- Forzar adjudicación manual (solo debugging)
- Activar siguiente sesión en la serie
- Ver logs recientes del motor

EXTREMADAMENTE ÚTIL para testing y auditoría técnica.
"""

import streamlit as st

from backend_core.services.session_repository import session_repository
from backend_core.services.session_engine import session_engine
from backend_core.services.adjudicator_engine import adjudicator_engine
from backend_core.services.audit_repository import audit_repository


def render_admin_engine():

    st.title("⚙️ Panel Motor — Admin Engine")
    st.markdown("""
Herramientas internas para operar el motor de Compra Abierta.

**⚠️ Solo para entornos de staging / desarrollo.**
En producción debe estar protegido.
""")

    st.divider()

    # =====================================================
    # MOTOR DE EXPIRACIÓN
    # =====================================================
    st.header("⏳ Motor de Expiración (5 días)")

    if st.button("🔁 Ejecutar motor de expiración ahora"):
        session_engine.process_expired_sessions()
        st.success("Motor de expiración ejecutado.")
        st.experimental_rerun()

    st.caption("Esto simula el worker automático que corre cada minuto.")

    st.divider()

    # =====================================================
    # ADJUDICACIÓN MANUAL (DEBUG)
    # =====================================================
    st.header("🎯 Adjudicación manual (debug)")

    session_id = st.text_input("ID de sesión para adjudicar manualmente:")

    if st.button("⚠️ Forzar adjudicación manual"):
        if not session_id.strip():
            st.error("Introduce un session_id válido.")
        else:
            result = adjudicator_engine.adjudicate_session(session_id.strip())
            if result:
                st.success(f"Adjudicación realizada. Ganador: {result['user_id']}")
            else:
                st.error("No se pudo adjudicar (ver logs).")

    st.divider()

    # =====================================================
    # ROLLING MANUAL
    # =====================================================
    st.header("🔄 Activar siguiente sesión de la serie (rolling)")

    roll_session_id = st.text_input("ID de sesión para activar siguiente:")

    if st.button("▶️ Activar siguiente sesión"):
        if not roll_session_id.strip():
            st.error("Introduce un session_id válido.")
        else:
            session = session_repository.get_session_by_id(roll_session_id.strip())
            if not session:
                st.error("Sesión no encontrada.")
            else:
                activated = session_engine.activate_next_session_in_series(session)
                if activated:
                    st.success(f"Siguiente sesión activada: {activated['id']}")
                else:
                    st.warning("No se encontró siguiente sesión parked en la serie.")

    st.divider()

    # =====================================================
    # LOGS DEL MOTOR
    # =====================================================
    st.header("📜 Logs del motor (últimos 200 eventos)")

    logs = audit_repository.get_logs(limit=200)

    if not logs:
        st.info("No hay logs disponibles.")
        return

    for item in logs:
        with st.expander(f"[{item['action']}]  —  {item['created_at']}"):
            st.json(item)
