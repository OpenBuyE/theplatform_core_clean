"""
chains.py
Vista de series y cadenas de sesiones.

Responsabilidades:
- Listar sesiones agrupadas por series_id
- Ordenar las sesiones por sequence_number
- Manejo seguro de valores None o inválidos
"""

import streamlit as st

from backend_core.services.session_repository import session_repository


def render_chains():
    st.title("🔗 Cadenas de Sesiones (Series)")

    st.write(
        """
Esta vista agrupa todas las sesiones por su `series_id`  
y muestra cómo se encadenan en orden de `sequence_number`.
"""
    )

    st.divider()

    # Obtener TODAS las sesiones (parked, active, finished)
    sessions = session_repository.get_sessions(limit=500)

    if not sessions:
        st.info("No hay sesiones registradas.")
        return

    # Agrupar por series_id
    chains = {}
    for s in sessions:
        sid = s.get("series_id") or "SIN_SERIE"
        if sid not in chains:
            chains[sid] = []
        chains[sid].append(s)

    # Ordenación robusta
    def safe_seq_number(sess):
        """
        Devuelve el sequence_number si existe y es int.
        Si es None, lo empuja al final.
        """
        seq = sess.get("sequence_number")
        if isinstance(seq, int):
            return seq
        return 999999999  # valor grande para mandar al final

    # Ordenar cada serie:
    for sid in chains:
        chains[sid] = sorted(chains[sid], key=safe_seq_number)

    # Renderizado
    for series_id, series_sessions in chains.items():
        with st.expander(f"📦 Serie: {series_id}"):
            for s in series_sessions:
                st.write(
                    f"- **Sesión:** {s['id']} "
                    f" | producto `{s.get('product_id')}` "
                    f" | seq `{s.get('sequence_number')}` "
                    f" | estado `{s.get('status')}`"
                )
