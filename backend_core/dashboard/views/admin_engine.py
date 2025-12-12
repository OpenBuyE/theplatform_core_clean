# backend_core/dashboard/views/admin_engine.py

import streamlit as st
import requests


# =========================================================
# 🧠 ADMIN ENGINE — MOTOR DETERMINISTA PRO
# =========================================================

def render_admin_engine():
    st.title("🧠 Admin Engine — Motor Determinista PRO")

    # -----------------------------------------------------
    # Seguridad: solo admin_master
    # -----------------------------------------------------
    role = st.session_state.get("role")
    if role != "admin_master":
        st.error("Acceso restringido. Solo Admin Master.")
        return

    st.markdown(
        """
        Este panel permite:

        • Disparar manualmente el **motor determinista PRO** (vía Modal, cuando esté activo)  
        • Verificar adjudicaciones mediante **replay determinista + auditoría criptográfica**

        ⚠️ En producción, la adjudicación debe ejecutarse automáticamente.
        """
    )

    st.markdown("---")

    # =====================================================
    # 🚀 DISPARO MANUAL DEL MOTOR (Modal)
    # =====================================================
    st.subheader("🚀 Ejecutar adjudicación determinista (Modal)")

    modal_url = st.secrets.get("MODAL_ADJUDICATION_URL")

    if not modal_url:
        st.warning(
            "MODAL_ADJUDICATION_URL no configurado. "
            "Puedes continuar usando Replay & Verify sin Modal."
        )
    else:
        limit = st.number_input(
            "Número máximo de sesiones a adjudicar",
            min_value=1,
            max_value=50,
            value=10,
            step=1,
        )

        if st.button("🚀 Ejecutar motor determinista"):
            with st.spinner("Ejecutando motor determinista PRO en Modal…"):
                try:
                    response = requests.post(
                        modal_url,
                        json={"limit": limit},
                        timeout=60,
                    )

                    if response.status_code != 200:
                        st.error(f"Error HTTP {response.status_code}")
                        st.text(response.text)
                        return

                    data = response.json()

                except Exception as e:
                    st.error(f"Error llamando a Modal: {e}")
                    return

            st.success("Motor ejecutado correctamente")

            st.markdown("### 📊 Resultado")
            st.write("🕒 Timestamp:", data.get("timestamp"))
            st.write("⚙️ Engine:", data.get("engine"))
            st.metric("Sesiones procesadas", data.get("processed_count", 0))

            if data.get("processed"):
                st.markdown("#### ✅ Sesiones adjudicadas")
                st.code("\n".join(data["processed"]))

            if data.get("skipped"):
                st.markdown("#### ⏭️ Sesiones omitidas")
                st.code("\n".join(data["skipped"]))

            if data.get("errors"):
                st.markdown("#### ❌ Errores")
                for err in data["errors"]:
                    st.error(f"{err['session_id']}: {err['error']}")

    st.markdown("---")

    # =====================================================
    # 🔎 REPLAY & VERIFY — AUDITORÍA PRO
    # =====================================================
    st.subheader("🔎 Replay & Verify — Auditoría determinista PRO")

    st.markdown(
        """
        Esta herramienta **recalcula la adjudicación** desde los datos históricos
        y verifica que **coincide exactamente** con lo almacenado en base de datos.

        ✔ Sin azar  
        ✔ Reproducible  
        ✔ Auditable  
        """
    )

    session_id = st.text_input("Session ID a verificar (UUID)")

    if st.button("✅ Verificar adjudicación (Replay)"):
        if not session_id.strip():
            st.error("Introduce un Session ID válido.")
            return

        from backend_core.services.adjudication_replay_service import replay_and_verify

        try:
            report = replay_and_verify(session_id.strip())
            st.write(report)

            status = report.get("status")

            if status == "VERIFIED":
                st.success(
                    "VERIFIED ✅ Coincide base de datos vs motor determinista PRO "
                    "(winner + inputs_hash + proof_hash)."
                )
            elif status == "NO_STORED_ADJUDICATION":
                st.warning(
                    "No existe adjudicación almacenada para esta sesión. "
                    "El resultado mostrado es solo el recalculado."
                )
            else:
                st.error(
                    "MISMATCH ❌ Hay discrepancias entre la adjudicación almacenada "
                    "y el replay del motor."
                )

        except Exception as e:
            st.error(f"Error durante Replay & Verify: {e}")

    st.markdown("---")
    st.info(
        "Este panel no contiene lógica crítica. "
        "El motor determinista vive fuera del dashboard."
    )

