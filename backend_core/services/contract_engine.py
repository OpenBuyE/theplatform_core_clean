"""
contract_engine.py
Motor contractual de la sesión de compra colectiva.

Este módulo NO mueve dinero ni habla directamente con la Fintech.
Su función es:

- Registrar, de forma estructurada y auditable, los hitos contractuales
  definidos en el "Contrato de participación en sesión de compra colectiva":

  1) Creación de la operación contractual al adjudicar la sesión
  2) Confirmación de que todos los depósitos son válidos
  3) Autorización de pago al proveedor (OK de la OÜ)
  4) Pago efectivo del proveedor (confirmado por Fintech)
  5) Entrega / recogida del producto al adjudicatario
  6) Caso excepcional de fuerza mayor: devolución SOLO del precio de producto
"""

from datetime import datetime
from typing import Dict, List, Optional

from .supabase_client import supabase
from .session_repository import session_repository
from .audit_repository import log_event


CONTRACT_TABLE = "session_contracts"  # opcional, de momento usamos solo audit_logs


class ContractEngine:
    """
    Motor lógico-contractual. Toda la verdad legal queda reflejada en audit_logs.

    En el futuro se puede mapear a una tabla específica (session_contracts),
    pero de momento nos basta con eventos de auditoría bien definidos.
    """

    # =====================================================
    # 1) Creación de la "operación contractual" al adjudicar
    # =====================================================
    def on_session_awarded(
        self,
        session: Dict,
        participants: List[Dict],
        awarded_participant: Dict,
    ) -> None:
        """
        Este método se llama UNA sola vez por sesión,
        justo después de que el motor determinista haya elegido adjudicatario.

        Aquí registramos:
        - qué sesión
        - quiénes eran los participantes
        - quién es el adjudicatario
        - que la Fintech tiene los depósitos en custodia
        """

        session_id = session["id"]
        awarded_user_id = awarded_participant["user_id"]

        log_event(
            action="contract_session_awarded",
            session_id=session_id,
            user_id=awarded_user_id,
            metadata={
                "participants": [
                    {
                        "participant_id": p["id"],
                        "user_id": p["user_id"],
                        "amount": p.get("amount"),
                        "price": p.get("price"),
                        "quantity": p.get("quantity"),
                    }
                    for p in participants
                ],
                "awarded_participant_id": awarded_participant["id"],
                "awarded_user_id": awarded_user_id,
                "contract_step": "SESSION_AWARDED",
            }
        )

    # =====================================================
    # 2) Confirmación: todos los depósitos OK (Fintech)
    # =====================================================
    def on_all_deposits_confirmed(self, session_id: str) -> None:
        """
        Punto de enganche cuando la Fintech confirma que TODOS los pagos
        del grupo comprador son válidos (no hay tarjetas fallidas, chargebacks, etc).

        Esta confirmación es clave: si falta un depósito, la sesión NO es válida.
        """

        log_event(
            action="contract_all_deposits_confirmed",
            session_id=session_id,
            metadata={
                "contract_step": "ALL_DEPOSITS_CONFIRMED"
            }
        )

    # =====================================================
    # 3) OK de la OÜ para pagar al proveedor
    # =====================================================
    def on_ou_authorizes_supplier_payment(self, session_id: str) -> None:
        """
        Punto donde la OÜ (operadora) da el visto bueno formal a la Fintech
        para pagar la factura proforma del proveedor.

        Aquí todavía NO pagamos; simplemente queda constancia de la autorización.
        """

        log_event(
            action="contract_ou_authorizes_supplier_payment",
            session_id=session_id,
            metadata={
                "contract_step": "OU_AUTHORIZES_SUPPLIER_PAYMENT"
            }
        )

    # =====================================================
    # 4) Pago efectivo al proveedor (Fintech)
    # =====================================================
    def on_supplier_paid(
        self,
        session_id: str,
        proforma_invoice_id: Optional[str] = None
    ) -> None:
        """
        La Fintech confirma que ha pagado la factura (proforma o definitiva)
        al proveedor del producto.

        En este punto, el precio del producto ha salido de la Fintech
        hacia el proveedor.
        """

        log_event(
            action="contract_supplier_paid",
            session_id=session_id,
            metadata={
                "contract_step": "SUPPLIER_PAID",
                "proforma_invoice_id": proforma_invoice_id,
            }
        )

    # =====================================================
    # 5) Entrega / recogida del producto por el adjudicatario
    # =====================================================
    def on_product_delivered(
        self,
        session_id: str,
        awarded_user_id: str
    ) -> None:
        """
        DMHG confirma que el adjudicatario ha recogido el producto en tienda
        (o lo ha recibido, si en el futuro contemplamos envíos).

        Muy importante a efectos de cierre definitivo de la operación.
        """

        log_event(
            action="contract_product_delivered",
            session_id=session_id,
            user_id=awarded_user_id,
            metadata={
                "contract_step": "PRODUCT_DELIVERED"
            }
        )

    # =====================================================
    # 6) Caso excepcional: fuerza mayor, proveedor no entrega
    # =====================================================
    def on_force_majeure_refund_product_price(
        self,
        session_id: str,
        awarded_user_id: str,
        product_price_amount: float,
    ) -> None:
        """
        ESCENARIO EXCEPCIONAL:

        - El proveedor no puede entregar el producto (fuerza mayor, cierre, etc).
        - La OÜ decide activar la cláusula de fuerza mayor/resolución.
        - La Fintech devuelve SOLO el importe del PRECIO DEL PRODUCTO
          al adjudicatario final.

        NO se devuelven:
        - comisión OÜ
        - gastos de gestión
        """

        log_event(
            action="contract_force_majeure_refund_product_price",
            session_id=session_id,
            user_id=awarded_user_id,
            metadata={
                "contract_step": "FORCE_MAJEURE_REFUND_PRODUCT_PRICE",
                "refund_amount_product_price": product_price_amount,
            }
        )


# Instancia global
contract_engine = ContractEngine()
