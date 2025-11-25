# backend_core/dashboard/views/category_manager_pro.py

import streamlit as st

from backend_core.services.product_repository_v2 import (
    list_categories,
    create_category,
    update_category,
    delete_category,
)


def render_category_manager_pro():
    st.title("📂 Category Manager PRO")
    st.caption("Gestiona categorías en categorias_v2")

    st.markdown("---")

    # ==========================
    # CREAR NUEVA CATEGORÍA
    # ==========================

    st.subheader("➕ Crear nueva categoría")

    with st.form("create_category_form", clear_on_submit=True):
        nombre = st.text_input("Nombre de la categoría", max_chars=120)
        descripcion = st.text_area(
            "Descripción (opcional)",
            placeholder="Descripción interna o pública de la categoría",
            height=80,
        )

        submitted = st.form_submit_button("Crear categoría")

    if submitted:
        if not nombre:
            st.error("El nombre de la categoría es obligatorio.")
        else:
            ok = create_category(nombre=nombre, descripcion=descripcion or None)
            if ok:
                st.success(f"Categoría '{nombre}' creada correctamente.")
                st.experimental_rerun()
            else:
                st.error("Error creando la categoría.")

    st.markdown("---")

    # ==========================
    # LISTADO + EDICIÓN / BORRADO
    # ==========================

    st.subheader("📋 Categorías existentes")

    categories = list_categories()

    if not categories:
        st.info("No hay categorías registradas.")
        return

    for cat in categories:
        _render_category_row(cat)


def _render_category_row(cat: dict):
    """
    Renderiza una categoría con edición inline y botón de borrado.
    """
    cat_id = cat.get("id")
    nombre_actual = cat.get("categoria") or "(sin nombre)"
    descripcion_actual = cat.get("descripcion") or ""

    with st.expander(f"📁 {nombre_actual} — {cat_id}"):

        st.markdown(f"**ID:** `{cat_id}`")

        # FORM DE EDICIÓN
        with st.form(f"edit_cat_{cat_id}"):
            nuevo_nombre = st.text_input(
                "Nombre",
                value=nombre_actual,
                max_chars=120,
            )
            nueva_desc = st.text_area(
                "Descripción",
                value=descripcion_actual,
                height=80,
            )

            col1, col2 = st.columns([1, 1])
            with col1:
                guardar = st.form_submit_button("💾 Guardar cambios")
            with col2:
                borrar = st.form_submit_button("🗑 Borrar categoría")

        # POST-ACCIONES
        if guardar:
            if not nuevo_nombre:
                st.error("El nombre no puede estar vacío.")
            else:
                ok = update_category(
                    category_id=cat_id,
                    nombre=nuevo_nombre,
                    descripcion=nueva_desc,
                )
                if ok:
                    st.success("Categoría actualizada correctamente.")
                    st.experimental_rerun()
                else:
                    st.error("Error actualizando la categoría.")

        if borrar:
            confirm = st.checkbox(
                f"Confirmo que quiero borrar la categoría '{nombre_actual}'",
                key=f"confirm_delete_{cat_id}",
            )
            if confirm:
                ok = delete_category(cat_id)
                if ok:
                    st.warning(f"Categoría '{nombre_actual}' borrada.")
                    st.experimental_rerun()
                else:
                    st.error("Error borrando la categoría.")
            else:
                st.info("Marca la casilla de confirmación antes de borrar.")
