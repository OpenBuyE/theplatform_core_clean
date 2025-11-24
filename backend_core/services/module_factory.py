# backend_core/services/module_factory.py

from __future__ import annotations

from typing import List, Dict, Any
from datetime import datetime

from backend_core.services.supabase_client import table
from backend_core.services.audit_repository import log_event
from backend_core.services.module_repository import (
    create_module,
)
from backend_core.services.session_repository import (
    create_parked_session,
)
from backend_core.services.session_engine import session_engine


MODULES_TABLE = "ca_modules"
BATCHES_TABLE = "ca_module_batches"


class ModuleFactory:
    """
    Crea módulos de sesión en lote, permitiendo que un operador genere
    N módulos idénticos de un producto (p.ej. 20 PS5).
    
    Cada módulo generado automáticamente:
    - queda vinculado a un batch_id
    - crea una serie y su primera sesión parked
    - queda listo para rolling y adjudicación
    """

    # ============================================================
    # 1) CREAR BATCH
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

        # 1) Crear registro de batch
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

        # 2) Generar módulos uno a uno
        for i in range(units):
            mod = self.create_single_module(
                product_id=product_id,
                module_code=module_code,
                organization_id=organization_id,
                batch_id=batch_id,
            )
            created_modules.append(mod)

        # 3) Actualizar batch con unidades generadas
        (
            table(BATCHES_TABLE)
            .update({"generated_units": len(created_modules)})
            .eq("id", batch_id)
            .execute()
        )

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
    # 2) CREAR MÓDULO ÚNICO
    # ============================================================

    def create_single_module(
        self,
        product_id: str,
        module_code: str,
        organization_id: str,
        batch_id: str = None,
    ) -> Dict[str, Any]:
        """
        Crea un módulo único:
        - Inserta módulo en ca_modules
        - Crea serie
        - Crea primera sesión parked
        """

        # 1) Crear módulo base
        module = create_module(
            product_id=product_id,
            module_code=module_code,
            organization_id=organization_id,
            batch_id=batch_id,
        )

        module_id = module["id"]

        # 2) Crear serie y primera sesión parked
        session = create_parked_session(
            product_id=product_id,
            organization_id=organization_id,
            module_id=module_id,
        )

        log_event(
            "module_created",
            session_id=session["id"],
            metadata={
                "module_id": module_id,
                "module_code": module_code,
                "product_id": product_id,
                "batch_id": batch_id,
            },
        )

        return {
            "module": module,
            "first_session": session,
        }

    # ============================================================
    # 3) CREAR MÚLTIPLES MÓDULOS (ATENCIÓN: no usa batches)
    # ============================================================

    def create_multiple_modules(
        self,
        product_id: str,
        module_code: str,
        organization_id: str,
        units: int,
    ) -> List[Dict[str, Any]]:
        """
        Genera N módulos idénticos, sin crear un batch.
        Útil para test, pero en producción usar create_batch.
        """

        result = []
        for _ in range(units):
            mod = self.create_single_module(
                product_id, module_code, organization_id
            )
            result.append(mod)

        return result

    # ============================================================
    # 4) CANCELAR MÓDULO
    # ============================================================

    def cancel_module(self, module_id: str, reason: str):
        """
        Cancela un módulo:
        - Cambia module_status a 'cancelled'
        - Guarda motivo
        - Detiene rolling (si aplica)
        """

        now = datetime.utcnow().isoformat()

        resp = (
            table(MODULES_TABLE)
            .update(
                {
                    "module_status": "cancelled",
                    "cancel_reason": reason,
                }
            )
            .eq("id", module_id)
            .execute()
        )

        log_event(
            "module_cancelled",
            session_id=None,
            metadata={"module_id": module_id, "reason": reason},
        )

        return resp.data[0] if resp.data else None

    # ============================================================
    # 5) ARCHIVAR MÓDULO
    # ============================================================

    def archive_module(self, module_id: str):
        """
        Archiva un módulo manualmente.
        """

        now = datetime.utcnow().isoformat()

        resp = (
            table(MODULES_TABLE)
            .update(
                {
                    "module_status": "archived",
                    "archived_at": now,
                }
            )
            .eq("id", module_id)
            .execute()
        )

        log_event(
            "module_archived",
            session_id=None,
            metadata={"module_id": module_id},
        )

        return resp.data[0] if resp.data else None

    # ============================================================
    # 6) MARCAR MÓDULO SIN ADJUDICATARIO
    # ============================================================

    def mark_no_award(self, module_id: str):
        """
        Marca un módulo como sin adjudicatario.
        """

        resp = (
            table(MODULES_TABLE)
            .update({"has_award": False, "module_status": "no_award"})
            .eq("id", module_id)
            .execute()
        )

        log_event(
            "module_no_award",
            session_id=None,
            metadata={"module_id": module_id},
        )

        return resp.data[0] if resp.data else None


# Instancia global
module_factory = ModuleFactory()
