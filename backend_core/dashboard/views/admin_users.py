import streamlit as st

from backend_core.services.acl import (
    require_org,
    require_permission
)

from backend_core.services.user_repository import (
    list_users,
    list_users_in_org,
    add_user_to_org
)

from backend_core.services.auth_repository import (
    register_user_with_password
)

from backend_core.services.context import get_current_org


@require_org
@require_permission("admin.manage_users")
def render_admin_users():

    st.header("👥 Gestión de Usuarios de la Organización")

    org_id = get_current_org()
    if not org_id:
        st.error("No hay organización activa.")
        return

    st.markdown("## 👤 Usuarios dentro de esta organización")

    rows = list_users_in_org(org_id)

    if not rows:
        st.info("No hay usuarios asignados a esta organización.")
    else:
        for u in rows:
            user = u.get("users", {})
            role = u.get("roles", {}).get("name", u.get("role", "-"))

            st.markdown(f"### 🧑 {user.get('name', 'Desconocido')}")
            st.write(f"**Email:** {user.get('email','-')}")
            st.write(f"**Rol:** `{role}`")
            st.write(f"**Asignado:** {u.get('created_at', '-')}")
            st.markdown("---")

    st.markdown("## ➕ Añadir usuario a la organización")

    with st.expander("Crear y asignar un nuevo usuario", expanded=False):
        with st.form("create_user_form"):
            name = st.text_input("Nombre completo")
            email = st.text_input("Email")
            password = st.text_input("Contraseña", type="password")
            role = st.selectbox("Rol", ["admin", "operator", "viewer"])

            submit = st.form_submit_button("Crear usuario y asignar")

            if submit:
                if not name or not email or not password:
                    st.error("Todos los campos son obligatorios.")
                else:
                    # 1) Crear usuario + credenciales
                    auth_result = register_user_with_password(
                        name=name,
                        email=email,
                        password=password
                    )

                    if not auth_result:
                        st.error("No se pudo crear el usuario.")
                        return

                    # 2) Recuperar user_id desde public.users
                    new_user_id = auth_result["user_id"]

                    # 3) Asignarlo a la organización
                    link = add_user_to_org(
                        user_id=new_user_id,
                        org_id=org_id,
                        role_name=role
                    )

                    if link:
                        st.success("Usuario creado y asignado correctamente.")
                        st.experimental_rerun()
                    else:
                        st.error("El usuario se creó, pero no se pudo asignar a la organización.")

    st.markdown("## 🔁 Asignar usuario EXISTENTE a esta organización")

    # Listado de usuarios globales
    all_users = list_users()

    # Filtrar usuarios no asignados ya a esta organización
    existing_ids = {u["user_id"] for u in rows}
    available = [u for u in all_users if u["id"] not in existing_ids]

    with st.expander("Asignar usuario existente", expanded=False):
        if not available:
            st.info("Todos los usuarios ya están asignados.")
        else:
            with st.form("assign_existing_user"):
                user_choice = st.selectbox(
                    "Selecciona un usuario",
                    [f"{u['name']} ({u['email']})" for u in available]
                )

                role = st.selectbox("Rol", ["admin", "operator", "viewer"])

                submit_assign = st.form_submit_button("Asignar a organización")

                if submit_assign:
                    selected = available[
                        [f"{u['name']} ({u['email']})" for u in available].index(user_choice)
                    ]
                    user_id = selected["id"]

                    link = add_user_to_org(
                        user_id=user_id,
                        org_id=org_id,
                        role_name=role
                    )

                    if link:
                        st.success("Usuario asignado correctamente.")
                        st.experimental_rerun()
                    else:
                        st.error("No se pudo asignar el usuario a la organización.")
