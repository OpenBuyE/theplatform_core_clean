# server.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers API
from backend_core.api import fintech_routes
from backend_core.api import internal_routes


app = FastAPI(
    title="Compra Abierta API",
    version="1.0.0",
)

# -----------------------------
# CORS (ajusta para producción)
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # en producción -> restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Healthcheck
# -----------------------------
@app.get("/health", tags=["health"])
async def healthcheck():
    return {"status": "ok"}


# -----------------------------
# Routers
# -----------------------------

# Webhooks Fintech
app.include_router(fintech_routes.router)

# Rutas internas (contratos, administración interna, devtools)
app.include_router(internal_routes.router)

# Aquí puedes añadir más routers:
# from backend_core.api import session_routes, admin_routes, users_routes
# app.include_router(session_routes.router)
