import streamlit as st
from backend_core.services.supabase_client import table

def render_operator_debug():
    st.title("🧪 Operator Debug — Ver contenido real de ca_operators")

    st.markdown("Esto muestra **exactamente** lo que devuelve Supabase.")

    try:
        result = table("ca_operators").select("*").execute()
    except Exception as e:
        st.error(f"❌ Error ejecutando consulta Supabase: {e}")
        return

    # Mostrar estructura del objeto
    st.subheader("Raw result object:")
    st.write(result)

    # Mostrar .data si existe
    if hasattr(result, "data"):
        st.subheader("Resultado en result.data:")
        st.write(result.data)

    # Mostrar como lista final
    rows = []
    if hasattr(result, "data"):
        rows = result.data or []
    elif isinstance(result, list):
        rows = result
    else:
        rows = []

    st.subheader("Filas interpretadas:")
    st.write(rows)

    if not rows:
        st.warning("⚠ Supabase devuelve 0 filas en ca_operators.")
    else:
        st.success(f"Hay {len(rows)} filas en ca_operators.")
