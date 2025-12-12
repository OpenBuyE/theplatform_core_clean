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
        • Generar **Proof Bundles auditables** (IP / Patente / Notaría)

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
            "Puedes continuar usando Replay & Verify y Proof Bundles sin Modal."
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
        Recalcula la adjudicación a partir de snapshots históricos
        y verifica que **coincide exactamente** con lo persistido.

        ✔ Sin azar  
        ✔ Reproducible  
        ✔ Auditable  
        """
    )

    session_id_verify = st.text_input(
        "Session ID a verificar (UUID)",
        key="replay_verify_session_id",
        placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    )

    if st.button("✅ Verificar adjudicación (Replay determinista)"):
        if not session_id_verify.strip():
            st.error("Introduce un Session ID válido.")
            return

        try:
            from backend_core.services.adjudication_replay_verify_pro import (
                replay_verify_session,
            )

            with st.spinner("Recalculando adjudicación determinista…"):
                report = replay_verify_session(session_id_verify.strip())

            st.markdown("### 📄 Informe de verificación")
            st.json(report.__dict__)

            if report.matches:
                st.success(
                    "VERIFIED ✅ Coincidencia total entre DB y motor determinista PRO."
                )
            else:
                st.error(
                    f"MISMATCH ❌\n\nMotivo: {report.reason}"
                )

        except Exception as e:
            st.error(f"Error durante Replay & Verify: {e}")

    st.markdown("---")

    # =====================================================
    # 📦 PROOF BUNDLE — IP / PATENTE
    # =====================================================
    st.subheader("📦 Proof Bundle — Evidencia IP / Patente")

    st.markdown(
        """
        Genera un **Proof Bundle determinista** autocontenido, apto para:

        • Registro de Propiedad Intelectual  
        • Patente (algoritmo / sistema)  
        • Notaría / sellado temporal  
        • Auditoría legal y técnica  

        El bundle incluye:
        - Snapshots mínimos
        - Contexto congelado del algoritmo
        - Evidencias criptográficas
        - Replay verificado
        """
    )

    session_id_bundle = st.text_input(
        "Session ID para generar Proof Bundle (UUID)",
        key="proof_bundle_session_id",
        placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    )

    col1, col2 = st.columns(2)
    with col1:
        include_participants = st.checkbox(
            "Incluir snapshot mínimo de participantes",
            value=True,
        )
    with col2:
        strict_verify = st.checkbox(
            "Verificación estricta (DB vs Replay)",
            value=True,
        )

    if st.button("📦 Generar Proof Bundle"):
        if not session_id_bundle.strip():
            st.error("Introduce un Session ID válido.")
            return

        try:
            from backend_core.services.adjudication_proof_bundle_pro import (
                build_proof_bundle_for_session,
            )

            with st.spinner("Generando Proof Bundle determinista…"):
                pb = build_proof_bundle_for_session(
                    session_id_bundle.strip(),
                    include_participants=include_participants,
                    strict_verify=strict_verify,
                )

            st.success("Proof Bundle generado correctamente")

            st.markdown("### 🔐 Hash criptográfico del bundle")
            st.code(pb.bundle_hash)

            st.markdown("### 📄 Contenido del Proof Bundle")
            st.json(pb.bundle)

            st.download_button(
                label="⬇️ Descargar Proof Bundle (JSON canónico)",
                data=pb.canonical_json,
                file_name=f"proof_bundle_{session_id_bundle.strip()}.json",
                mime="application/json",
            )

        except Exception as e:
            st.error(f"Error generando Proof Bundle: {e}")

    st.markdown("---")
    st.info(
        "Este panel **no contiene lógica crítica**.\n\n"
        "El motor determinista, la adjudicación y la auditoría viven fuera del dashboard."
    )
