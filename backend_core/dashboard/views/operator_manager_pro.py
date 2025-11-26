import streamlit as st
import bcrypt
import uuid
from backend_core.services.supabase_client import table


# ---------------------------------------------------------
#  UTILS
# ---------------------------------------------------------

def hash_password(password: str) -> str:
    """
    Genera un hash bcrypt para almacenar la contraseña.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()


def require_admin():
    """
    Bloquea acceso a operadores que no tienen rol admin_master o god.
    """
    role = st.session_state.get("role")
    if role not in ["admin_master", "god"]:
        st.error("⛔ Acceso denegado. Se requiere rol admin_master o god.")
        st.stop()


# ---------------------------------------------------------
#  CRUD FUNCTIONS
# ---------------------------------------------------------

def list_operators():
    try:
        result = table("ca_operators").select("*").execute()
        return result
    except Exception as e:
        st.error(f"Error cargando operadores: {e}")
        return []


def create_operator(data: dict):
    try:
        table("ca_operators").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error creando operador: {e}")
        return False


def update_operator(operator_id: str, data: dict):
    try:
        table("ca_operators").update(data).eq("id", operator_id).execute()
        return True
    except Exception as e:
        st.error(f"Error actualizando operador: {e}")
        return False


# ---------------------------------------------------------
#  MAIN VIEW
# ---------------------------------------------------------

def render_operator_manager_pro():
    st.title("👥 Operator Manager Pro")

    # Requiere administrador
    require_admin()

    st.markdown("### Gestión avanzada de operadores")
    st.markdown("Administre usuarios internos, roles, contraseñas y países.")

    st.markdown("---")

    # -----------------------------------------------------
    # SECCIÓN 1 — CREAR OPERADOR
    # -----------------------------------------------------
    st.subheader("➕ Crear Operador")

    with st.form("create_operator_form"):
        email = st.text_input("Email / Usuario")
        full_name = st.text_input("Nombre completo")
        name = st.text_input("Nombre corto (obligatorio si la tabla lo pide)")

        password = st.text_input("Contraseña", type="password")
        role = st.selectbox("Rol", ["operator", "supervisor", "admin_master", "god"])

        country_options = ["ES", "PT", "FR", "IT", "DE", "NL", "BE", "UK"]
        allowed_countries = st.multiselect("Países asignados", country_options)

        global_access = st.checkbox("Acceso global a todos los países", value=False)
        active = st.checkbox("Activo", value=True)

        submit = st.form_submit_button("Crear operador")

        if submit:
            if not email or not name or not full_name or not password:
                st.error("Todos los campos son obligatorios.")
            else:
                hashed_pw = hash_password(password)
                new_id = str(uuid.uuid4())

                data = {
                    "id": new_id,
                    "email": email,
                    "name": name,
                    "full_name": full_name,
                    "password_hash": hashed_pw,
                    "role": role,
                    "allowed_countries": allowed_countries,
                    "global_access": global_access,
                    "active": active,
                    "organization_id": "00000000-0000-0000-0000-000000000001"
                }

                if create_operator(data):
                    st.success(f"Operador creado correctamente: {email}")
                    st.experimental_rerun()

    st.markdown("---")

    # -----------------------------------------------------
    # SECCIÓN 2 — LISTADO DE OPERADORES
    # -----------------------------------------------------
    st.subheader("📋 Lista de Operadores")

    operators = list_operators()

    if not operators:
        st.info("No hay operadores registrados.")
        return

    # Mostrar tabla
    st.dataframe(
        [
            {
                "ID": op["id"],
                "Email": op["email"],
                "Name": op.get("name"),
                "Full Name": op.get("full_name"),
                "Rol": op.get("role"),
                "Países": ", ".join(op.get("allowed_countries", [])),
                "Global": op.get("global_access"),
                "Activo": op.get("active"),
            }
            for op in operators
        ],
        width=None,
        height=350
    )

    st.markdown("---")

    # -----------------------------------------------------
    # SECCIÓN 3 — EDITAR OPERADOR
    # -----------------------------------------------------
    st.subheader("✏️ Editar Operador")

    operator_ids = [op["id"] for op in operators]
    op_id = st.selectbox("Seleccione operador", operator_ids)

    op_data = next((o for o in operators if o["id"] == op_id), None)

    if not op_data:
        st.error("No se pudo cargar el operador seleccionado.")
        return

    st.markdown(f"**Editando:** {op_data['email']}")

    with st.form("edit_operator_form"):
        full_name = st.text_input("Nombre completo", value=op_data.get("full_name"))
        name = st.text_input("Nombre corto", value=op_data.get("name"))
        role = st.selectbox("Rol", ["operator", "supervisor", "admin_master", "god"], index=["operator", "supervisor", "admin_master", "god"].index(op_data.get("role", "operator")))

        country_options = ["ES", "PT", "FR", "IT", "DE", "NL", "BE", "UK"]
        allowed_countries = st.multiselect("Países asignados", country_options, default=op_data.get("allowed_countries", []))

        global_access = st.checkbox("Acceso global", value=op_data.get("global_access", False))
        active = st.checkbox("Activo", value=op_data.get("active", True))

        new_password = st.text_input("Nueva contraseña (opcional)", type="password")

        submit_edit = st.form_submit_button("Guardar cambios")

        if submit_edit:
            update_data = {
                "full_name": full_name,
                "name": name,
                "role": role,
                "allowed_countries": allowed_countries,
                "global_access": global_access,
                "active": active,
            }

            if new_password:
                update_data["password_hash"] = hash_password(new_password)

            if update_operator(op_id, update_data):
                st.success("Operador actualizado correctamente.")
                st.experimental_rerun()
