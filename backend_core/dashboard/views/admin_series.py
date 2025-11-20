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


@require_org
@require_permission("admin.manage_users")  # usamos este permiso como "admin general"
def render_admin_series():
    st.header("🧩 Series de Sesiones")

    # -------------------------
    #   Listado de series
    # -------------------------
    st.subheader("📜 Series existentes")

    series = list_session_series()

    if not series:
        st.info("No hay series definidas todavía para esta organización.")
    else:
        for s in series:
            st.markdown(f"### 🔹 {s.get('code', '')} – {s.get('name','')}")
            st.write(f"**Módulo:** `{s.get('module_id','-')}` (ID)")
            st.write(f"**Producto:** {s.get('product_id','-')}")
            st.write(f"**Descripción:** {s.get('product_description','-')}")
            st.write(f"**Precio unitario:** {s.get('unit_price','-')} {s.get('currency','EUR')}")
            st.write(f"**Aforo máximo:** {s.get('max_pax','-')}")
            st.write(f"**Umbral de activación:** {s.get('activation_threshold','-')}")
            st.write(f"**Lugar:** {s.get('location','-')}")
            st.write(f"**Creada:** {s.get('created_at','-')}")
            st.markdown("---")

    # -------------------------
    #   Crear nueva serie
    # -------------------------
    st.subheader("➕ Crear nueva serie de sesiones")

    modules = list_session_modules()
    if not modules:
        st.error("No hay módulos de sesión definidos. Revisa la tabla session_modules.")
        return

    module_labels = [f"{m['code']} – {m.get('label','')}" for m in modules]
    module_by_label = {lbl: m for lbl, m in zip(module_labels, modules)}

    with st.form("create_series_form"):
        code = st.text_input("Código de serie", help="Ejemplo: X23")
        name = st.text_input("Nombre descriptivo", help="Ejemplo: Sesión X23 – Compra recurrente")
        module_label = st.selectbox("Módulo de sesión", module_labels)

        product_id = st.text_input("ID / código de producto", "")
        product_description = st.text_area("Descripción del producto", "")

        col1, col2 = st.columns(2)
        with col1:
            unit_price = st.number_input("Precio unitario", min_value=0.0, step=0.01)
            max_pax = st.number_input("Aforo máximo (pax)", min_value=0, step=1)
        with col2:
            currency = st.text_input("Moneda", value="EUR")
            activation_threshold = st.number_input(
                "Umbral de activación (pax mínimos)",
                min_value=0,
                step=1,
                help="Número mínimo de participantes para activar la sesión."
            )

        location = st.text_input("Lugar", "")

        submitted = st.form_submit_button("Crear serie")

        if submitted:
            if not code or not name:
                st.error("El código y el nombre de la serie son obligatorios.")
            else:
                module = module_by_label[module_label]
                module_id = module["id"]

                payload = {
                    "code": code,
                    "name": name,
                    "module_id": module_id,
                    "product_id": product_id or None,
                    "product_description": product_description or None,
                    "unit_price": unit_price if unit_price > 0 else None,
                    "currency": currency or "EUR",
                    "max_pax": int(max_pax) if max_pax > 0 else None,
                    "activation_threshold": int(activation_threshold) if activation_threshold > 0 else None,
                    "location": location or None,
                }

                created = create_session_series(payload)

                if created:
                    st.success("Serie creada correctamente.")
                    st.experimental_rerun()
                else:
                    st.error("No se pudo crear la serie.")
