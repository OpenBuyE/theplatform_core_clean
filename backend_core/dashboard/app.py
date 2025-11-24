# backend_core/dashboard/app.py
import streamlit as st

def main():
    st.set_page_config(page_title="Platform Core - Safe Boot", layout="wide")
    st.title("🟦 Platform Core — Safe Boot Mode")
    st.write("La app ha arrancado correctamente. El menú completo está temporalmente desactivado.")
    st.info("Ahora podemos reactivar las vistas una a una sin bloquear Streamlit.")

if __name__ == "__main__":
    main()
