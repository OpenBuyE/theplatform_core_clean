import bcrypt
from backend_core.services.supabase_client import supabase

def login_operator(email: str, password: str):
    """
    Login robusto: case-insensitive, limpio, seguro.
    """
    try:
        clean_email = email.strip()

        # Búsqueda insensible a mayúsculas/minúsculas
        result = (
            supabase.table("ca_operators")
            .select("*")
            .ilike("email", clean_email)
            .execute()
        )

        if not result or not result.data:
            return None  # operador no encontrado

        operator = result.data[0]

        if not operator.get("active", False):
            return None  # inactivo

        stored_hash = operator.get("password_hash")
        if not stored_hash:
            return None  # sin contraseña

        # Verificación BCRYPT
        if isinstance(password, str):
            password = password.encode("utf-8")

        if bcrypt.checkpw(password, stored_hash.encode("utf-8")):
            return operator

        return None  # contraseña incorrecta

    except Exception as e:
        print("Error en login_operator:", e)
        return None
