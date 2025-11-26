import streamlit as st
from backend_core.services.supabase_client import table
from backend_core.services.operator_repository import (
    get_operator_by_id,
    get_operator_allowed_countries,
    operator_has_global_access,
)

# ------------------------------------------------------------
# LOGIN DE OPERADORES (simple)
# Selección manual desde tabla ca_operators
# ------------------------------------------------------------

def render_operator_login():
    st.title("🔐 Login Operadores")

    # 1. Obtener lista de operadores desde Supabase
    resp = table("ca_operators").select("id, role, name").execute()
    rows = resp.data if hasattr(resp, "data") else resp.get("data") or []

    if not rows:
        st.error("No hay operadores en la base de datos.")
        return

    # 2. Selección manual
    labels = [f"{op['name']} ({op['role']})" if op.get("name") else f"{op['id']} ({op['role']})" for op in rows]
    selected = st.selectbox("Seleccione operador:", options=list(range(len(rows))), format_func=lambda i: labels[i])

    operator = rows[selected]

    if st.button("Iniciar sesión como operador"):
        operator_id = operator["id"]
        full_operator = get_operator_by_id(operator_id)

        st.session_state["operator_id"] = operator_id
        st.session_state["role"] = full_operator.get("role")

        allowed = get_operator_allowed_countries(operator_id)
        st.session_state["allowed_countries"] = allowed

        st.session_state["global_access"] = operator_has_global_access(full_operator)

        st.success(f"Sesión iniciada como: {full_operator.get('name', operator_id)}")
        st.info(f"Países permitidos: {allowed if allowed else 'GLOBAL'}")
