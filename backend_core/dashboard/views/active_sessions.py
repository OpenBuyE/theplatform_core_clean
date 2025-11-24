# backend_core/dashboard/views/active_sessions.py

import streamlit as st
from datetime import datetime

from backend_core.services.session_repository import (
    get_active_sessions,
)
from backend_core.services.participant_repository import (
    add_test_participant,
    get_participants_for_session,
)
from backend_core.services.adjudicator_engine import adjudicator_engine
from backend_core.services.product_repository import get_product
from backend_core.services.module_repository import get_session_module


# =======================================================
# ACTIVE SESSIONS — VISTA PROFESIONAL
# =======================================================

def render_active_sessions():

    st.header("🔥 Active Sessions")

    sessions = get_active_sessions()

    if not sessions:
        st.info("No hay sesiones activas.")
        return

    for s in sessions:

        st.markdown("---")
        st.subheader(f"Sesión {s['id']}")

        # ================================================
        # MÓDULO ASIGNADO
        # ================================================
        module = get_session_module(s)
        st.write(f"**Módulo:** {module['module_code']} — {module['name']}")

        # ================================================
        # MOSTRAR PRODUCTO
        # ================================================
        product = get_product(s["product_id"])
        if product:
            st.write(f"📦 Producto: **{product['name']}** — {product['price']} €")
            if product.get("image_url"):
                st.image(product["image_url"], width=200)

        st.write(f"Organization: {s['organization_id']}")
        st.write(f"Status: {s['status']}")

        # ================================================
        # MÓDULO C — PRELAUNCH
        # ================================================
        if module["module_code"] == "C_PRELAUNCH":
            st.warning("🔒 Este módulo NO permite participantes ni activación.")
            st.write("Modo pre-lanzamiento / anuncio.")
            continue

        # ================================================
        # MÓDULO B — AUTO-EXPIRE
        # ================================================
        if module["module_code"] == "B_AUTO_EXPIRE":
            st.info("Este módulo expira automáticamente. No tiene adjudicación ni pagos.")

            expires_at = s.get("expires_at")
            if expires_at:
                now = datetime.utcnow()
                remaining = (expires_at - now).total_seconds()
                st.write(f"⏳ Expira en: **{int(remaining/60)} min**")

            # Mostrar participantes pero no adjudicación
            participants = get_participants_for_session(s["id"])
            st.write(f"Pax registrados: {len(participants)}/{s['capacity']}")

            st.write("Participantes:")
            st.json(participants)

            continue  # NO adjudicación ni añadir participante de test

        # ================================================
        # MÓDULO A — DETERMINISTA
        # ================================================
        if module["module_code"] == "A_DETERMINISTIC":

            st.success("Módulo determinista activo.")

            # Mostramos aforo
            pax = s["pax_registered"]
            st.write(f"Aforo: {pax}/{s['capacity']}")

            # Participantes
            participants = get_participants_for_session(s["id"])
            st.write("Participantes:")
            st.json(participants)

            # ---------------------------------------------
            # Botón: Añadir participante test
            # ---------------------------------------------
            if st.button(f"Añadir participante test — Sesión {s['id']}"):
                add_test_participant(
                    session_id=s["id"],
                    user_id="test-user",
                    amount=product["price"] / s["capacity"],
                    price=product["price"],
                    quantity=1,
                )
                st.success("Participante de test añadido.")

            # ---------------------------------------------
            # Botón: Forzar adjudicación
            # ---------------------------------------------
            if st.button(f"FORZAR ADJUDICACIÓN — {s['id']}"):
                adjudicator_engine.execute_adjudication(s["id"])
                st.success("Adjudicación ejecutada.")

            continue
