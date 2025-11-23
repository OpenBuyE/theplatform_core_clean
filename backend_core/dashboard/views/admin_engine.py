# backend_core/dashboard/views/admin_engine.py

import streamlit as st
import requests

API_BASE = "http://localhost:8000"   # Ajusta si es necesario


def render_admin_engine():
    st.title("Admin Engine")
    st.write("Herramientas de diagnóstico del motor (API / health / debug).")

    # Healthcheck
    if st.button("🔎 Comprobar /health"):
        try:
            resp = requests.get(f"{API_BASE}/health", timeout=5)
            st.success(resp.json())
        except Exception as e:
            st.error(f"Error al llamar /health: {e}")

    st.subheader("Información")
    st.write(
        """
        - Esta sección está pensada para pruebas internas.
        - Aquí puedes añadir botones para:
            - reindexar seeds,
            - lanzar tests internos,
            - inspeccionar estados de las máquinas de pagos, etc.
        """
    )
