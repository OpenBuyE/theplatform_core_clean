"""
admin_seeds.py
Vista de administración de seeds de adjudicación para Compra Abierta.

Permite:
- Ver la seed pública asociada a una sesión
- Crear / actualizar la seed pública
- Eliminar la seed (la sesión pasará a usar solo seed interna)

Se apoya en:
- backend_core.services.adjudicator_repository
- backend_core.services.session_repository
"""

import streamlit as st

from backend_core.services.adjudicator_repository import adjudicator_repository
from backend_core.services.session_repository import session_repository


def _build_session_label(session: dict) -> str:
    """
    Construye una etiqueta legible para el selector de sesiones.
    """
    seq = session.get("sequence_number", "-")
    product_id = session.get("product_id", "-")
    status = session.get("status", "-")
    series_id = session.get("series_id", "") or ""
    short_series = series_id[:8] + "…" if series_id else "-"

    return (
        f"[{status.upper()}] "
        f"Seq {seq} | Prod {product_id} | Serie {short_series} | id={session['id']}"
    )


def render_admin_seeds():
    st.title("🔑 Admin Seeds — Motor Determinista")

    st.markdown(
        """
Esta vista te permite gestionar las **seeds públicas** usadas por el
motor determinista de adjudicación.

- Si **NO hay seed pública**, la sesión usa solo **seed interna** (datos de la propia sesión).
- Si **hay seed pública**, la seed efectiva será: `PUBLIC + BASE`.

Puedes:
- Ver la seed actual de una sesión
- Crear / actualizar la seed pública
- Eliminar la seed y volver al modo solo interno
        """
    )

    st.divider()

    # ---------------------------------------------------------
    # Filtros básicos de sesiones
    # ---------------------------------------------------------
    col_status, col_org = st.columns(2)

    with col_status:
        status_filter = st.selectbox(
            "Estado de sesión",
            options=["todas", "parked", "active", "finished"],
            index=1,  # por defecto "parked" o "active", puedes ajustar
        )

    with col_org:
        organization_id = st.text_input(
            "Filtrar por organization_id (opcional)",
            value=""
        ).strip() or None

    # Cargar sesiones
    if status_filter == "todas":
        sessions = session_repository.get_sessions(
            status=None,
            organization_id=organization_id,
            limit=200
        )
    else:
        sessions = session_repository.get_sessions(
            status=status_filter,
            organization_id=organization_id,
            limit=200
        )

    if not sessions:
        st.info("No se han encontrado sesiones con los filtros actuales.")
        return

    # Mapa etiqueta -> sesión
    label_to_session = {
        _build_session_label(s): s for s in sessions
    }

    st.subheader("Selecciona sesión")

    selected_label = st.selectbox(
        "Sesiones disponibles",
        options=list(label_to_session.keys()),
    )

    session = label_to_session[selected_label]
    session_id = session["id"]

    st.markdown("### 🧩 Detalle de la sesión seleccionada")
    info_cols = st.columns(3)
    with info_cols[0]:
        st.write("**ID**")
        st.code(session_id, language="text")
    with info_cols[1]:
        st.write("**Estado**")
        st.write(session.get("status"))
        st.write("**Seq**:", session.get("sequence_number"))
    with info_cols[2]:
        st.write("**Producto**")
        st.write(session.get("product_id"))
        st.write("**Serie**")
        st.code(session.get("series_id") or "-", language="text")

    st.divider()

    # ---------------------------------------------------------
    # Seed actual
    # ---------------------------------------------------------
    st.subheader("🔐 Seed pública actual")

    current_seed = adjudicator_repository.get_public_seed_for_session(session_id)

    if current_seed:
        st.success("Esta sesión tiene una seed pública configurada.")
        st.code(current_seed, language="text")
    else:
        st.warning(
            "Esta sesión **no tiene seed pública**. "
            "El motor usará solo la seed interna derivada de los datos de la sesión."
        )

    st.divider()

    # ---------------------------------------------------------
    # Formulario: crear / actualizar seed
    # ---------------------------------------------------------
    st.subheader("✏️ Crear / actualizar seed pública")

    with st.form("set_seed_form"):
        new_seed = st.text_input(
            "Nueva seed pública",
            value=current_seed or "",
            placeholder="Ejemplo: bloque_123456, hash_externo_XYZ, etc."
        )

        submitted = st.form_submit_button("💾 Guardar / actualizar seed")

        if submitted:
            cleaned = new_seed.strip()
            if cleaned == "":
                st.error("La seed pública no puede estar vacía. Usa el botón de eliminación si quieres quitarla.")
            else:
                adjudicator_repository.set_public_seed_for_session(session_id, cleaned)
                st.success("Seed pública actualizada correctamente.")
                st.experimental_rerun()

    st.divider()

    # ---------------------------------------------------------
    # Botón: eliminar seed (volver a solo interna)
    # ---------------------------------------------------------
    st.subheader("🧹 Eliminar seed pública")

    st.markdown(
        """
Si eliminas la seed pública:

- La sesión **seguirá existiendo**.
- El motor volverá a usar **solo seed interna**.
- Esto puede cambiar el adjudicatario futuro si la sesión todavía no se ha adjudicado.
        """
    )

    col_del1, col_del2 = st.columns(2)

    with col_del1:
        confirm_delete = st.checkbox(
            "Confirmo que quiero eliminar la seed pública de esta sesión"
        )

    with col_del2:
        if st.button("🗑 Eliminar seed pública"):
            if not confirm_delete:
                st.error("Marca la casilla de confirmación antes de eliminar la seed.")
            else:
                adjudicator_repository.delete_seed_for_session(session_id)
                st.success("Seed pública eliminada. La sesión usará solo seed interna.")
                st.experimental_rerun()
