"""
contract_engine.py
Motor contractual de Compra Abierta.

Responsabilidades:
- Verificar que todos los depósitos de la sesión están autorizados.
- Activar adjudicación determinista cuando:
    * sesión tiene aforo completo
    * todos los depósitos están "AUTHORIZED"
- Integrarse con wallet_orchestrator / fintech en pasos posteriores
- Gestionar settlement y casos de fuerza mayor

Este módulo NO tiene imports circulares.
"""

from typing import List, Dict, Optional
from datetime import datetime

from .session_repository import session_repository
from .participant_repository import participant_repository
from .adjudicator_engine import adjudicator_engine
from .audit_repository import log_event


class ContractEngine:
    """
    Motor contractual general del sistema.
    """

    # -----------------------------------------------------
    # 1) Verificar si una sesión está lista para adjudicar
    # -----------------------------------------------------
    def _are_all_deposits_authorized(
        self,
        session_id: str,
        participants: List[Dict]
    ) -> bool:
        """
        Comprueba si TODOS los participantes de la sesión
        tienen depósitos autorizados (wallet + fintech).

        Esta versión inicial se basa en:
        - Los eventos de wallet (deposit authorized)
        - El campo participant["deposit_status"] (si existe)
        - Metadata del auditor (futuro)

        De momento asumimos que:
        - participant["amount"] es válido
        - participant["deposit_status"] == "AUTHORIZED"
        """

        for p in participants:
            status = p.get("deposit_status")
            if status != "AUTHORIZED":
                return False

        return True

    # -----------------------------------------------------
    # 2) Motor principal que chequea si se debe adjudicar
    # -----------------------------------------------------
    def try_adjudicate_session(self, session_id: str) -> Optional[Dict]:
        """
        Lógica principal del motor contractual.

        Flujo:
        - Cargar sesión
        - Si no está 'active' o no tiene aforo completo → no adjudica
        - Obtener lista de participantes
        - Verificar que TODOS los depósitos están OK
        - Llamar adjudicator_engine para seleccionar adjudicatario
        """

        session = session_repository.get_session_by_id(session_id)
        if not session:
            log_event("contract_error_session_not_found", session_id=session_id)
            return None

        # 1. La sesión debe estar activa
        if session["status"] != "active":
            log_event("contract_session_not_active", session_id=session_id)
            return None

        # 2. Debe tener aforo completo
        capacity = session.get("capacity")
        registered = session.get("pax_registered")

        if registered != capacity:
            log_event(
                "contract_not_full_capacity",
                session_id=session_id,
                metadata={"registered": registered, "capacity": capacity}
            )
            return None

        # 3. Obtener todos los participantes
        participants = participant_repository.get_participants_by_session(session_id)
        if not participants:
            log_event("contract_no_participants", session_id=session_id)
            return None

        # 4. Verificar depósitos autorizados
        if not self._are_all_deposits_authorized(session_id, participants):
            log_event(
                "contract_deposits_not_authorized",
                session_id=session_id,
                metadata={"participants": len(participants)}
            )
            return None

        # 5. Ejecutar adjudicación determinista
        adjudicatario = adjudicator_engine.adjudicate_session(session_id)

        if not adjudicatario:
            log_event("contract_adjudication_failed", session_id=session_id)
            return None

        # 6. Marcar sesión como finalizada
        now = datetime.utcnow().isoformat()
        session_repository.mark_session_as_finished(session_id, now)

        log_event(
            "contract_adjudication_completed",
            session_id=session_id,
            metadata={"awarded_user_id": adjudicatario["user_id"]}
        )

        return adjudicatario

    # -----------------------------------------------------
    # 3) Liquidación final tras adjudicación
    # -----------------------------------------------------
    def on_settlement_completed(
        self,
        session_id: str,
        adjudicatario_id: str,
        fintech_batch_id: str,
    ):
        """
        Se llama cuando la Fintech confirma liquidación:
        - Pago al proveedor
        - Pago comisiones
        - Pago gastos de gestión
        """

        log_event(
            "contract_settlement_completed",
            session_id=session_id,
            user_id=adjudicatario_id,
            metadata={"fintech_batch_id": fintech_batch_id}
        )

    # -----------------------------------------------------
    # 4) Caso de fuerza mayor (solo se devuelve el precio)
    # -----------------------------------------------------
    def on_force_majeure_refund(
        self,
        session_id: str,
        adjudicatario_id: str,
        product_amount: float,
        currency: str,
        reason: Optional[str]
    ):
        """
        El proveedor NO puede entregar el producto.
        La Fintech devuelve al adjudicatario:
        - Solo precio del producto
        """

        log_event(
            "contract_force_majeure",
            session_id=session_id,
            user_id=adjudicatario_id,
            metadata={
                "product_amount": product_amount,
                "currency": currency,
                "reason": reason,
            }
        )


# Instancia global
contract_engine = ContractEngine()
