# backend_core/services/module_factory.py

from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime

from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event
from backend_core.services.module_repository import create_module
from backend_core.services.session_repository import create_parked_session
from backend_core.services.session_engine import session_engine


MODULES_TABLE = "ca_modules"
BATCHES_TABLE = "ca_module_batches"
SERIES_TABLE = "ca_session_series"


class ModuleFactory:
    """
    Crea módulos y lotes de módulos (batches).
    Cada módulo:
        - crea un registro en ca_modules
        - genera su propia serie en ca_session_series
        - genera la primera sesión parked con sequence_number = 1
        - queda listo para rolling + adjudicación determinista
    """

    # ============================================================
    # 1) CREAR BATCH COMPLETO
    # ============================================================

    def create_batch(
        self,
        product_id: str,
        module_code: str,
        organization_id: str,
        units: int,
    ) -> Dict[str, Any]:
        """
        Crea un batch que agrupa N módulos idénticos.
        """

        if units <= 0:
            raise ValueError("units debe ser > 0")

        # 1. Crear el batch
        resp = (
            table(BATCHES_TABLE)
            .insert(
                {
                    "product_id": product_id,
                    "module_code": module_code,
                    "organization_id": organization_id,
                    "requested_units": units,
                    "generated_units": 0,
                }
            )
            .execute()
        )

        batch = resp.data[0]
        batch_id = batch["id"]

        created_modules = []

        # 2. Generar cada módulo
        for _ in range(units):
            mod = self.create_single_module(
                product_id=product_id,
                module_code=module_code,
                organization_id=organization_id,
                batch_id=batch_id,
            )
            created_modules.append(mod)

        # 3. Actualizar unidades generadas
        (
            table(BATCHES_TABLE)
            .update({"generated_units": len(created_modules)})
            .eq("id", batch_id)
            .execute()
        )

        # 4. Registrar auditoría
        log_event(
            "module_batch_created",
            session_id=None,
            metadata={
                "batch_id": batch_id,
                "product_id": product_id,
                "module_code": module_code,
                "units_requested": units,
                "units_generated": len(created_modules),
            },
        )

        return {
            "batch": batch,
            "modules": created_modules,
        }

    # ============================================================
    # 2) CREAR UN MÓDULO ÚNICO
    # ============================================================

    def create_single_module(
        self,
        product_id: str,
        module_code: str,
        organization_id: str,
        batch_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Crea un módulo:
            - inserta en ca_modules
            - crea serie en ca_session_series
            - crea sesión parked inicial (sequence=1)
        """

        # 1. Crear módulo base
        module = create_module(
            product_id=product_id,
            module_code=module_code,
            organization_id=organization_id,
            batch_id=batch_id,
        )

        module_id = module["id"]

        # 2. Crear serie (ca_session_series)
        series = (
            table(SERIES_TABLE)
            .insert(
                {
                    "product_id": product_id,
                    "organization_id": organization_id,
                    "module_id": module_id,
                }
            )
            .execute()
        ).data[0]

        series_id = series["id"]

        # 3. Crear primera sesión parked (sequence_number = 1)
        #    Usamos la firma correcta de create_parked_session:
        #    (product_id, organization_id, series_id, sequence_number, capacity, expires_in_days, module_code, module_id)
        first_session = create_parked_session(
            product_id=product_id,
            organization_id=organization_id,
            series_id=series_id,
            sequence_number=1,
            capacity=1,  # ¡ATENCIÓN! Se debe actualizar cuando tengamos capacity real del producto
            expires_in_days=5,
            module_code=module_code,
            module_id=module_id,
        )

        log_event(
            "module_created_and_initialized",
            session_id=first_session["id"],
            metadata={
                "module_id": module_id,
                "module_code": module_code,
                "series_id": series_id,
                "product_id": product_id,
                "batch_id": batch_id,
            },
        )

        return {
            "module": module,
            "series": series,
            "first_session": first_session,
        }

    # ============================================================
    # 3) CREAR MÚLTIPLES MÓDULOS SIN BATCH (solo testing)
    # ============================================================

    def create_multiple_modules(
        self,
        product_id: str,
        module_code: str,
        organization_id: str,
        units: int,
    ) -> List[Dict[str, Any]]:
        """
        Genera N módulos idénticos sin crear batch.
        """

        output = []

        for _ in range(units):
            mod = self.create_single_module(
                product_id=product_id,
                module_code=module_code,
                organization_id=organization_id,
                batch_id=None,
            )
            output.append(mod)

        return output

    # ============================================================
    # 4) CANCELAR MÓDULO
    # ============================================================

    def cancel_module(self, module_id: str, reason: str):
        """
        Cancela un módulo manualmente.
        """

        now = datetime.utcnow().isoformat()

        resp = (
            table(MODULES_TABLE)
            .update(
                {
                    "module_status": "cancelled",
                    "cancel_reason": reason,
                    "updated_at": now,
                }
            )
            .eq("id", module_id)
            .execute()
        )

        log_event("module_cancelled", session_id=None, metadata={"module_id": module_id, "reason": reason})

        return resp.data[0] if resp.data else None

    # ============================================================
    # 5) ARCHIVAR MÓDULO
    # ============================================================

    def archive_module(self, module_id: str):
        now = datetime.utcnow().isoformat()

        resp = (
            table(MODULES_TABLE)
            .update(
                {
                    "module_status": "archived",
                    "archived_at": now,
                    "updated_at": now,
                }
            )
            .eq("id", module_id)
            .execute()
        )

        log_event("module_archived", session_id=None, metadata={"module_id": module_id})

        return resp.data[0] if resp.data else None

    # ============================================================
    # 6) MARCAR SIN ADJUDICATARIO
    # ============================================================

    def mark_no_award(self, module_id: str):
        resp = (
            table(MODULES_TABLE)
            .update({"module_status": "no_award", "has_award": False})
            .eq("id", module_id)
            .execute()
        )

        log_event("module_no_award", session_id=None, metadata={"module_id": module_id})

        return resp.data[0] if resp.data else None


# Instancia global
module_factory = ModuleFactory()
