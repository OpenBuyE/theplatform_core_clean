# server.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend_core.api import fintech_routes

app = FastAPI(
    title="Compra Abierta API",
    version="1.0.0",
)

# CORS (ajusta orígenes permitidos)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ajusta en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def healthcheck():
    return {"status": "ok"}


# Routers
app.include_router(fintech_routes.router)

# Aquí podrías incluir también:
# from backend_core.api import internal_routes, session_routes, admin_routes, ...
# app.include_router(internal_routes.router)
# app.include_router(session_routes.router)
