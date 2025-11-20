from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router as api_router

app = FastAPI(
    title="Compra Abierta — REST API",
    version="1.0.0",
    description="API pública para The Platform Core Clean"
)

# CORS básico (adaptar según frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ajustar en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Compra Abierta API Online",
        "version": "1.0.0"
    }
