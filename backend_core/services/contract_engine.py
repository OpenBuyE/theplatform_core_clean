"""
contract_engine.py
Motor contractual determinista para sesiones de Compra Abierta.

Este módulo NO toca dinero directamente ni hace llamadas a la Fintech.
Su responsabilidad es:

- Modelar las fases contractuales de una sesión de compra colectiva.
- Registrar en audit_logs todos los "pasos" que la OÜ valida:
  - Depósito autorizado en Fintech
  - Grupo válido / completo (todos pagos OK)
  - Adjudicación confirmada
  - Solicitud y recepción de factura proforma
  - Orden a Fintech para pagar al proveedor y distribuir comisiones
  - Confirmación de entrega del producto
  - Caso excepcional: fuerza mayor / proveedor no entrega → devolución SOLO del precio de producto al adjudicatario

El dinero:
- Siempre lo custodia y mueve la Fintech.
- Nunca pasa por el adjudicatario (solo recibe el producto).
- La OÜ no toca el dinero del producto (solo comisiones / gestión vía fintech).
"""

from datetime import datetime
from typing import Optional, Dict, Any

from .session_repository import session_repository
from .audit_repository import log_event


class ContractEngine:
    """
    Motor de orquestación contractual.
    Cada método representa un paso explícito del flujo del contrato.
    Todos los pasos se registran en audit_logs con un 'action' específico.
    """

    # ============================================================
    #  1) Depósitos individuales en Fintech (autorización)
    # ============================================================
    def record_deposit_authorized(
        self,
        session_id: str,
        participant_id: str,
        amount: float,
        currency: str = "EUR",
        fintech_ref: Optional[str] = None,
    ) -> None:
        """
        Paso: la Fintech confirma que ha autorizado el cargo en tarjeta
        y mantiene los fondos en depósito condicional.

        IMPORTANTE:
        - Esto NO significa todavía que el grupo sea válido.
        - Solo indica que este participante tiene su aportación bloqueada.
        """
        log_event(
            action="sc_deposit_authorized",
            session_id=session_id,
            metadata={
                "participant_id": participant_id,
                "amount": amount,
                "currency": currency,
                "fintech_ref": fintech_ref,
                "recorded_at": datetime.utcnow().isoformat(),
            },
        )

    # ============================================================
    #  2) Grupo válido / completo (todos pagos OK)
    # ============================================================
    def record_group_locked(
        self,
        session_id: str,
        reason: str = "capacity_reached_and_all_payments_valid",
    ) -> None:
        """
        Paso: la OÜ valida que el grupo es contractualmente válido.

        Condiciones (a nivel conceptual):
        - pax_registered == capacity (aforo completo)
        - TODAS las aportaciones están correctamente autorizadas/capturadas en la Fintech
          (si una falla, el grupo NO es válido).

        Aquí NO validamos técnicamente cada pago (eso será parte de la integración futura),
        solo registramos que la OÜ ha hecho esa validación.
        """
        session = session_repository.get_session_by_id(session_id)

        log_event(
            action="sc_group_locked",
            session_id=session_id,
            metadata={
                "reason": reason,
                "capacity": session.get("capacity") if session else None,
                "pax_registered": session.get("pax_registered") if session else None,
                "recorded_at": datetime.utcnow().isoformat(),
            },
        )

    # ============================================================
    #  3) Adjudicación determinista confirmada por la OÜ
    # ============================================================
    def record_adjudication_confirmed(
        self,
        session_id: str,
        adjudicatario_id: str,
        public_seed: Optional[str],
        internal_hash: str,
    ) -> None:
        """
        Paso: la OÜ confirma el resultado del motor determinista.

        - adjudicatario_id: identificador interno del adjudicatario en la sesión
        - public_seed: semilla pública utilizada (si existía)
        - internal_hash: hash determinista calculado por el motor
        """
        log_event(
            action="sc_adjudication_confirmed",
            session_id=session_id,
            metadata={
                "adjudicatario_id": adjudicatario_id,
                "public_seed": public_seed,
                "internal_hash": internal_hash,
                "recorded_at": datetime.utcnow().isoformat(),
            },
        )

    # ============================================================
    #  4) Solicitud y recepción de factura proforma
    # ============================================================
    def record_proforma_requested(
        self,
        session_id: str,
        provider_id: str,
        product_description: str,
    ) -> None:
        """
        Paso: la OÜ solicita al proveedor la factura proforma.
        (No implica todavía pago al proveedor.)
        """
        log_event(
            action="sc_proforma_requested",
            session_id=session_id,
            metadata={
                "provider_id": provider_id,
                "product_description": product_description,
                "requested_at": datetime.utcnow().isoformat(),
            },
        )

    def record_proforma_received(
        self,
        session_id: str,
        proforma_ref: str,
        total_product_price: float,
        management_fee: float,
        commission_fee: float,
        currency: str = "EUR",
    ) -> None:
        """
        Paso: la OÜ recibe la factura proforma del proveedor
        y valida el desglose económico.

        NOTA:
        - total_product_price = precio del bien (PVP IVA incl. del producto)
        - management_fee = gastos de gestión (sociedad española)
        - commission_fee = comisión operativa OÜ (sociedad estonia)
        """
        log_event(
            action="sc_proforma_received",
            session_id=session_id,
            metadata={
                "proforma_ref": proforma_ref,
                "total_product_price": total_product_price,
                "management_fee": management_fee,
                "commission_fee": commission_fee,
                "currency": currency,
                "received_at": datetime.utcnow().isoformat(),
            },
        )

    # ============================================================
    #  5) Orden a Fintech: pagar proveedor y distribuir comisiones
    # ============================================================
    def record_fintech_settlement_order(
        self,
        session_id: str,
        proforma_ref: str,
        total_product_price: float,
        management_fee: float,
        commission_fee: float,
        fintech_instruction_ref: Optional[str] = None,
        currency: str = "EUR",
    ) -> None:
        """
        Paso: la OÜ da el visto bueno a la Fintech para:

        - Pagar al proveedor el precio del producto.
        - Transferir a la sociedad española los gastos de gestión.
        - Transferir a la OÜ la comisión operativa.

        El flujo real de dinero lo ejecuta la Fintech, pero aquí dejamos constancia
        contractual de la instrucción.
        """
        log_event(
            action="sc_fintech_settlement_order",
            session_id=session_id,
            metadata={
                "proforma_ref": proforma_ref,
                "total_product_price": total_product_price,
                "management_fee": management_fee,
                "commission_fee": commission_fee,
                "currency": currency,
                "fintech_instruction_ref": fintech_instruction_ref,
                "ordered_at": datetime.utcnow().isoformat(),
            },
        )

    def record_fintech_settlement_confirmed(
        self,
        session_id: str,
        fintech_settlement_ref: str,
    ) -> None:
        """
        Paso: la Fintech confirma (a través de la OÜ) que:

        - El proveedor ha cobrado el producto.
        - Se han distribuido gastos de gestión y comisión.

        Aquí solo registramos la confirmación contractual.
        """
        log_event(
            action="sc_fintech_settlement_confirmed",
            session_id=session_id,
            metadata={
                "fintech_settlement_ref": fintech_settlement_ref,
                "confirmed_at": datetime.utcnow().isoformat(),
            },
        )

    # ============================================================
    #  6) Entrega / recogida del producto por el adjudicatario
    # ============================================================
    def record_product_delivered(
        self,
        session_id: str,
        adjudicatario_id: str,
        delivery_ref: Optional[str] = None,
        store_id: Optional[str] = None,
    ) -> None:
        """
        Paso: DMHG / proveedor confirman que el adjudicatario ha recogido el producto.

        - NO implica transacciones de dinero (ya se han hecho antes).
        - El adjudicatario solo recibe el producto, no dinero.
        """
        log_event(
            action="sc_product_delivered",
            session_id=session_id,
            metadata={
                "adjudicatario_id": adjudicatario_id,
                "delivery_ref": delivery_ref,
                "store_id": store_id,
                "delivered_at": datetime.utcnow().isoformat(),
            },
        )

    # ============================================================
    #  7) Caso excepcional: proveedor no puede entregar
    # ============================================================
    def record_force_majeure_refund_to_adjudicatario(
        self,
        session_id: str,
        adjudicatario_id: str,
        product_price_amount: float,
        reason: str,
        fintech_refund_ref: Optional[str] = None,
        currency: str = "EUR",
    ) -> None:
        """
        CASO EXCEPCIONAL:

        - El proveedor no puede entregar el producto (fuerza mayor, ruptura de stock irreversible, etc.).
        - La OÜ decide instruir a la Fintech para devolver SOLO el precio del producto
          al adjudicatario final.

        MUY IMPORTANTE:
        - No se devuelven ni la comisión ni los gastos de gestión.
        - Los demás participantes NO reciben devolución alguna.
        """
        log_event(
            action="sc_force_majeure_refund_to_adjudicatario",
            session_id=session_id,
            metadata={
                "adjudicatario_id": adjudicatario_id,
                "product_price_amount": product_price_amount,
                "currency": currency,
                "reason": reason,
                "fintech_refund_ref": fintech_refund_ref,
                "recorded_at": datetime.utcnow().isoformat(),
            },
        )


# Instancia exportable
contract_engine = ContractEngine()
