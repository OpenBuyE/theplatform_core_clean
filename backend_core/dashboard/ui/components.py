import streamlit as st


def session_card(session):
    st.markdown(f"""
    **ID:** {session.id}  
    **Operador:** {session.operator_id}  
    **Proveedor:** {session.supplier_id}  
    **Estado:** `{session.status}`  
    **Importe:** {session.amount} €
    ---
    """)
