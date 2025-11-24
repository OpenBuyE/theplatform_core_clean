# backend_core/services/contract_engine.py

from __future__ import annotations
from typing import Dict, Any, Optional

from backend_core.services.audit_repository import log_event
from backend_core.services.session_repository import get_session_by_id
from backend_core.services.module_repository import get_session_module
from backend_core.services.payment_state_machine import (
    init_payment_session,
    update_payment_state,
    get_payment_session,
)
from backend_core.services.wallet_orchestrator import wallet_orchestrator


class ContractEngine:
    """
    Motor contractual completo.
    AHORA integrado con módulos:
    - Solo Módulo A (Determinista) ejecuta contrato.
    - Módulo B y C deben ignorar completamente el flujo contractual.
    """

    # =====================================================================
    # LLAMADO ÚNICAMENTE DESPUÉS DE ADJUDICACIÓN (SOLO MÓDULO A)
    # =====================================================================
    def on_session_awarded(self, session_id: str, awarded_participant_id: str) -> None:
        """
        Empieza el contrato formal de la sesión.
        NO se ejecuta si el módulo NO es A_DETERMINISTIC.
        """

        session = get_session_by_id(session_id)
        module = get_session_module(session)

        if module["module_code"] != "A_DETERMINISTIC":
            log_event(
                "contract_blocked_by_module",
                session_id,
                metadata={"module": module["module_code"]},
            )
            return

        # Crear sesión contractual (estado inicial WAITING_DEPOSITS)
        init_payment_session(session_id, awarded_participant_id)

        log_event(
            "contract_started",
            session_id,
            metadata={"awarded_participant": awarded_participant_id},
        )

    # =====================================================================
    # EVENTO: DEPOSIT_OK DESDE FINTECH (SOLO MÓDULO A)
    # =====================================================================
    def on_participant_funded(self, session_id: str, payload: Dict[str, Any]) -> None:
        """
        Este evento se llama cuando MangoPay envía deposit-ok.
        Solo para módulo A.
        """

        session = get_session_by_id(session_id)
        module = get_session_module(session)

        if module["module_code"] != "A_DETERMINISTIC":
            log_event(
                "contract_funded_blocked_by_module",
                session_id,
                metadata={"module": module["module_code"]},
            )
            return

        update_payment_state(session_id, "DEPOSITS_OK")

        log_event("contract_deposit_ok", session_id, metadata=payload)

    # =====================================================================
    # EVENTO: SETTLEMENT (pago al proveedor)
    # =====================================================================
    def on_settlement_completed(self, session_id: str, payload: Dict[str, Any]) -> None:
        """
        Liquidación final: Fintech pagó al proveedor.
        Solo para módulo A.
        """

        session = get_session_by_id(session_id)
        module = get_session_module(session)

        if module["module_code"] != "A_DETERMINISTIC":
            log_event(
                "contract_settlement_blocked_by_module",
                session_id,
                metadata={"module": module["module_code"]},
            )
            return

        update_payment_state(session_id, "SETTLED")

        log_event("contract_settlement_completed", session_id, metadata=payload)

    # =====================================================================
    # EVENTO: FORCE MAJEURE
    # =====================================================================
    def on_force_majeure_refund(self, session_id: str, payload: Dict[str, Any]) -> None:
        """
        Caso excepcional: la fintech reembolsa el precio del producto.
        Solo Módulo A puede recibir este evento.
        """

        session = get_session_by_id(session_id)
        module = get_session_module(session)

        if module["module_code"] != "A_DETERMINISTIC":
            log_event(
                "contract_force_majeure_blocked_by_module",
                session_id,
                metadata={"module": module["module_code"]},
            )
            return

        update_payment_state(session_id, "FORCE_MAJEURE")

        log_event("contract_force_majeure_refund", session_id, metadata=payload)

    # =====================================================================
    # CONSULTA DE ESTADO CONTRACTUAL
    # =====================================================================
    def get_contract_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Devuelve el estado contractual + módulo asignado.
        """

        session = get_session_by_id(session_id)
        if not session:
            return None

        module = get_session_module(session)
        payment = get_payment_session(session_id)

        return {
            "session": session,
            "module": module,
            "payment": payment,
        }


contract_engine = ContractEngine()
