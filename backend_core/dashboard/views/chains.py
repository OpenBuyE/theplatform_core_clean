import streamlit as st

from backend_core.services.session_repository import session_repository


def render_chains():
    st.title("🔗 Series y Cadenas de Sesiones")

    st.markdown("""
    Esta vista muestra las series y secuencias de sesiones.
    Cada serie se identifica por `series_id`, y dentro de ella
    se listan las sesiones ordenadas por `sequence_number`.
    """)

    sessions = session_repository.get_sessions(limit=500)

    if not sessions:
        st.info("No hay sesiones registradas.")
        return

    # Agrupar por series_id
    series = {}
    for s in sessions:
        sid = s["series_id"]
        series.setdefault(sid, []).append(s)

    for sid, items in series.items():
        items_sorted = sorted(items, key=lambda x: x["sequence_number"])

        with st.expander(f"🔗 Serie {sid}"):
            for s in items_sorted:
                st.write(
                    f"**Seq {s['sequence_number']}** — "
                    f"Estado: {s['status']} — "
                    f"Aforo: {s['pax_registered']}/{s['capacity']}"
                )


