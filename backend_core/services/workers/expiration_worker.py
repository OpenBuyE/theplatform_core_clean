"""
expiration_worker.py
Worker automático para procesar expiración de sesiones
en Compra Abierta.

Ejecuta periódicamente:
    session_engine.process_expired_sessions()

Este worker debe ejecutarse en background:
    python expiration_worker.py

O mediante:
    pm2, supervisor, systemd, contenedor Docker, etc.
"""

import time
import traceback
from datetime import datetime

# Importar motor
from ..session_engine import session_engine
from ..audit_repository import log_event


# INTERVALO ENTRE EJECUCIONES
# ================================
# Recomendado: cada 60 segundos
INTERVAL_SECONDS = 60


def run_worker():
    """
    Bucle principal del worker.
    Llama al motor de expiración de sesiones cada X segundos.
    """

    log_event(
        action="expiration_worker_started",
        metadata={"interval_seconds": INTERVAL_SECONDS}
    )

    print("🔧 Expiration Worker iniciado.")
    print(f"⏳ Intervalo: {INTERVAL_SECONDS} segundos.")

    while True:
        try:
            now = datetime.utcnow().isoformat()

            print(f"[{now}] Ejecutando motor de expiración…")
            session_engine.process_expired_sessions()

            print(f"[{now}] ✓ Motor de expiración ejecutado correctamente.\n")

        except Exception as e:
            print("⚠️ Error en el worker de expiración:")
            traceback.print_exc()

            # Registrar error en auditoría
            log_event(
                action="expiration_worker_error",
                metadata={"error": str(e)}
            )

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    run_worker()
