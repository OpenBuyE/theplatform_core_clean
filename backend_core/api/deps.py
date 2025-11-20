"""
deps.py
Dependencias simples para FastAPI.

En el futuro podemos añadir:
- autenticación JWT
- API Keys
- control de organizaciones
"""

from fastapi import Header, HTTPException


async def api_key_required(x_api_key: str = Header(None)):
    """
    Validación simple basada en header: X-API-Key
    En producción debe sustituirse por JWT o control real de acceso.
    """
    # ⚠️ Ajustar según necesidad
    VALID_KEY = "TEST-API-KEY"

    if x_api_key != VALID_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return True
