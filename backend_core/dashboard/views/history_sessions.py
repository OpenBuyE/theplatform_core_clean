import streamlit as st

from backend_core.services.acl import require_org, require_permission
from backend_core.services.session_repository import (
    get_finished_sessions,
    get_participants_for_session,
)
from backend_core.services.adjudicator_engine import adjudicate_session


@require_org
@require_permission("session.view")
def render_history_sessions():
    st.header("📚 Histórico de Sesiones")

    sessions = get_finished_sessions()

    if not sessions:
        st.info("No hay sesiones finalizadas en esta organización.")
        return

    for s in sessions:
        sid = s["id"]
        st.subheader(f"📘 Sesión {sid}")

        st.write(f"**Serie:** {s.get('series_id','-')}")
        st.write(f"**Secuencia:** {s.get('sequence_number','-')}")
        st.write(f"**Activada:** {s.get('activated_at','-')}")
        st.write(f"**Finalizada:** {s.get('expires_at','-')}")

        # BOTÓN ADJUDICAR
        if st.button("✔ Adjudicar esta sesión", key=f"adj_{sid}"):
            result = adjudicate_session(sid)
            st.success("Sesión adjudicada correctamente.")
            st.json(result)
            st.experimental_rerun()

        # PARTICIPANTES
        participants = get_participants_for_session(sid)

        with st.expander("👥 Participantes / Compradores"):
            if not participants:
                st.info("No hubo participantes en esta sesión.")
            else:
                for p in participants:
                    adjud = "🏅 ADJUDICATARIO" if p.get("is_awarded") else ""
                    st.write(f"**Comprador:** {p['users']['name']} ({p['users']['email']})")
                    st.write(f"**Importe:** {p.get('amount','-')}")
                    st.write(f"**Precio:** {p.get('price','-')}")
                    st.write(f"**Cantidad:** {p.get('quantity','-')}")
                    st.write(f"{adjud}")
                    st.markdown("---")

        st.markdown("---")
