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
        • Verificar adjudicaciones mediante **Replay & Verify determinista + auditoría criptográfica**

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
    # 🔎 REPLAY & VERIFY — AUDITORÍA PRO (NUEVO BLOQUE)
    # =====================================================
    st.subheader("🔎 Replay & Verify — Auditoría determinista PRO")

    st.markdown(
        """
        Esta herramienta **recalcula la adjudicación** a partir de los snapshots históricos
        y verifica que **coincide exactamente** con la adjudicación persistida.

        ✔ Sin azar  
        ✔ Reproducible  
        ✔ Auditable  
        ✔ Legal-grade / IP-ready  
        """
    )

    session_id = st.text_input(
        "Session ID a verificar (UUID)",
        placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    )

    if st.button("✅ Verificar adjudicación (Replay determinista)"):
        if not session_id.strip():
            st.error("Introduce un Session ID válido.")
            return

        try:
            # Import explícito del servicio PRO
            from backend_core.services.adjudication_replay_verify_pro import (
                replay_verify_session,
            )

            with st.spinner("Recalculando adjudicación determinista…"):
                report = replay_verify_session(session_id.strip())

            # Presentación del reporte completo (audit-friendly)
            st.markdown("### 📄 Informe de verificación")
            st.json(report.__dict__)

            # Evaluación semántica
            if report.matches:
                st.success(
                    "VERIFIED ✅\n\n"
                    "La adjudicación almacenada coincide exactamente con el replay del motor "
                    "determinista PRO (awarded, hashes, ranking, versión de algoritmo)."
                )
            else:
                st.error(
                    f"MISMATCH ❌\n\n"
                    f"Motivo: {report.reason}\n\n"
                    "Existe una discrepancia entre la adjudicación persistida "
                    "y el resultado reproducido por el motor."
                )

        except Exception as e:
            st.error(f"Error durante Replay & Verify: {e}")

    st.markdown("---")
    st.info(
        "Este panel es exclusivamente de **orquestación y auditoría**.\n\n"
        "La lógica crítica del motor determinista vive fuera del dashboard."
    )
