"""
active_sessions.py
Vista de sesiones activas — versión adaptada al nuevo motor determinista.

Características:
- Lista sesiones activas
- Muestra estado, aforo, expiración
- Permite refrescar
- Permite activar siguiente sesión manualmente (debug)
"""

import streamlit as st

from backend_core.services.session_repository import session_repository
from backend_core.services.session_engine import session_engine
from backend_core.services.audit_repository import log_event


def render_active_sessions():
    st.title("🟢 Sesiones Activas")

    st.markdown(
        """
Esta tabla muestra todas las **sesiones activas** en el sistema.
Una sesión activa:
- Tiene un `expires_at` válido (máx 5 días).
- Puede finalizar por dos causas:
  1. Completar aforo → adjudicación inmediata (motor determinista)
  2. No completar aforo → expiración (motor de expiración)
        """
    )

    st.divider()

    # Obtener sesiones activas
    sessions = session_repository.get_sessions(status="active", limit=200)

    if not sessions:
        st.info("No hay sesiones activas en este momento.")
        return

    # Mostrar sesiones en tabla
    for s in sessions:
        with st.expander(f"🟢 Sesión {s['id']} — Producto {s['product_id']}"):
            st.write("**Estado:**", s["status"])
            st.write("**Aforo:**", f"{s['pax_registered']} / {s['capacity']}")
            st.write("**Sequence:**", s["sequence_number"])
            st.write("**Serie:**", s["series_id"])
            st.write("**Activada en:**", s.get("activated_at"))
            st.write("**Expira en:**", s.get("expires_at"))

            st.markdown("---")

            # ============================================================
            # Botón: Activar siguiente sesión (rolling manual)
            # ============================================================
            st.subheader("🔄 Rolling manual (debug)")

            if st.button(
                "Activar siguiente sesión en la serie",
                key=f"roll_{s['id']}"
            ):
                activated = session_engine.activate_next_session_in_series(s)

                if activated:
                    st.success(f"Siguiente sesión activada: {activated['id']}")
                    log_event(
                        action="ui_manual_rolling",
                        session_id=s["id"],
                        metadata={"activated_session_id": activated["id"]}
                    )
                    st.experimental_rerun()
                else:
                    st.warning("No existe siguiente sesión parked en la serie.")

            st.markdown("---")

            # Info debug (opcional)
            with st.expander("🔍 Debug info"):
                st.json(s)




