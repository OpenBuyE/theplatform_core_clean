import streamlit as st

from backend_core.services.session_repository import session_repository


def render_chains():
    st.title("🔗 Series y Cadenas de Sesiones")

    st.markdown("""
Aquí puedes visualizar las **series operativas**, es decir, 
las cadenas de sesiones que pertenecen a un mismo ciclo de producto.
""")

    st.divider()

    # Obtener todas las sesiones (limit alto)
    sessions = session_repository.get_sessions(limit=500)

    if not sessions:
        st.info("No hay sesiones registradas.")
        return

    # Agrupar por serie
    chains = {}
    for s in sessions:
        sid = s["series_id"]
        chains.setdefault(sid, []).append(s)

    # Ordenar sesiones por sequence_number
    for sid in chains:
        chains[sid] = sorted(chains[sid], key=lambda s: s["sequence_number"])

    # Renderizar cada serie
    for series_id, series_sessions in chains.items():
        st.subheader(f"🔗 Serie {series_id}")

        for sess in series_sessions:
            st.write(
                f"- **Sesión {sess['id']}** — "
                f"Seq: `{sess['sequence_number']}` — "
                f"Estado: `{sess['status']}` — "
                f"Aforo: {sess['pax_registered']}/{sess['capacity']}"
            )

        st.markdown("---")
