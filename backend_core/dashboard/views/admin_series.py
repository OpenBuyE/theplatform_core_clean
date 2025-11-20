import streamlit as st

from backend_core.services.acl import (
    require_org,
    require_permission,
)
from backend_core.services.module_repository import (
    list_session_series,
    list_session_modules,
    create_session_series,
)
from backend_core.services.session_engine import advance_series


@require_org
@require_permission("admin.manage_users")
def render_admin_series():
    st.header("🧩 Series de Sesiones")

    # -------------------------
    #   LISTADO DE SERIES
    # -------------------------
    st.subheader("📜 Series existentes")

    series = list_session_series()

    if not series:
        st.info("No hay series definidas todavía para esta organización.")
    else:
        for s in series:
            sid = s["id"]
            st.markdown(f"### 🔹 {s.get('code','')} – {s.get('name','')}")

            colA, colB = st.columns([3, 1])
            with colA:
                st.write(f"**Módulo:** `{s.get('module_id','-')}`")
                st.write(f"**Producto:** {s.get('product_id','-')}")
                st.write(f"**Descripción:** {s.get('product_description','-')}")
                st.write(f"**Precio unitario:** {s.get('unit_price','-')} {s.get('currency','EUR')}")
                st.write(f"**Aforo máximo:** {s.get('max_pax','-')} pax")
                st.write(f"**Umbral activación:** {s.get('activation_threshold','-')} pax")
                st.write(f"**Lugar:** {s.get('location','-')}")
                st.write(f"**Creada:** {s.get('created_at','-')}")

            with colB:
                if st.button("⏭️ Avanzar serie", key=f"advance_{sid}"):
                    result = advance_series(sid)
                    st.success("Serie avanzada correctamente.")
                    st.json(result)
                    st.experimental_rerun()

            st.markdown("---")

    # -------------------------
    #   CREAR NUEVA SERIE
    # -------------------------
    st.subheader("➕ Crear nueva serie de sesiones")

    modules = list_session_modules()
    if not modules:
        st.error("No hay módulos de sesión definidos en session_modules.")
        return

    module_labels = [f"{m['code']} – {m.get('label','')}" for m in modules]
    module_by_label = {lbl: m for lbl, m in zip(module_labels, modules)}

    with st.form("create_series_form"):
        code = st.text_input("Código de serie", help="Ej: X23")
        name = st.text_input("Nombre descriptivo")
        module_label = st.selectbox("Módulo de sesión", module_labels)

        product_id = st.text_input("ID / código de producto")
        product_description = st.text_area("Descripción del producto")

        col1, col2 = st.columns(2)
        with col1:
            unit_price = st.number_input("Precio unitario", min_value=0.0, step=0.01)
            max_pax = st.number_input("Aforo máximo", min_value=0, step=1)
        with col2:
            currency = st.text_input("Moneda", value="EUR")
            activation_threshold = st.number_input(
                "Umbral activación",
                min_value=0,
                step=1,
            )

        location = st.text_input("Lugar")

        submitted = st.form_submit_button("Crear serie")

        if submitted:
            module = module_by_label[module_label]
            module_id = module["id"]

            payload = {
                "code": code,
                "name": name,
                "module_id": module_id,
                "product_id": product_id,
                "product_description": product_description,
                "unit_price": unit_price,
                "currency": currency,
                "max_pax": int(max_pax),
                "activation_threshold": int(activation_threshold),
                "location": location,
            }

            created = create_session_series(payload)

            if created:
                st.success("Serie creada correctamente.")
                st.experimental_rerun()
            else:
                st.error("No se pudo crear la serie.")

