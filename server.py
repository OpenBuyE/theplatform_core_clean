"""
server.py
Servidor FastAPI principal para Compra Abierta.

Incluye:
- Rutas internas (API general)
- Rutas fintech
- Healthcheck
- CORS
- Documentación Swagger / Redoc
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --------------------------------------------
# Importar routers
# --------------------------------------------
from backend_core.api.api import api_router        # API general
from backend_core.api.fintech_routes import router as fintech_router


# --------------------------------------------
# Crear FastAPI app
# --------------------------------------------
app = FastAPI(
    title="Compra Abierta — Backend API",
    description="API principal del motor Compra Abierta.",
    version="1.0.0"
)

# --------------------------------------------
# Configurar CORS (permitimos todo en desarrollo)
# --------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # En producción limitar
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------
# Healthcheck
# --------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "message": "API viva"}


# --------------------------------------------
# Montar routers
# --------------------------------------------
app.include_router(api_router, prefix="/api")
app.include_router(fintech_router, prefix="/api")


# --------------------------------------------
# Modo local (solo se ejecuta si se llama directamente)
# --------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
