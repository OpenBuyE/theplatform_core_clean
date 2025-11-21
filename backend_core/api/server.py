from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router as api_router
from .fintech_routes import router as fintech_router


app = FastAPI(
    title="Compra Abierta — REST API",
    version="1.0.0",
    description="API pública para The Platform Core Clean (Compra Abierta)",
)

# CORS básico (ajusta allow_origins en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ ajustar en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas generales (sessions, participants, seeds, engine...)
app.include_router(api_router, prefix="/api")

# Rutas específicas Fintech (webhooks / notificaciones)
app.include_router(fintech_router, prefix="/api")


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Compra Abierta API Online",
        "version": "1.0.0",
    }

