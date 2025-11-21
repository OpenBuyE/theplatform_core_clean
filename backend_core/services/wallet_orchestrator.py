"""
wallet_orchestrator.py
Orquestador entre el motor contractual (contract_engine) y la Fintech (wallet_service).

OBJETIVO DE ESTA CAPA
---------------------
Este módulo NO habla directamente con tarjetas, bancos ni proveedores.
Su misión es:

- Recibir eventos de la Fintech (depósitos OK, pagos, incidencias).
- Registrar auditoría estructurada.
- Delegar en el motor contractual (contract_engine) la lógica de negocio.
- Dejar puntos de integración claros con wallet_service (MangoPay u otra).

VENTAJA: mantenemos el contrato y la lógica determinista de Compra Abierta
aislados de los detalles concretos de la API de la Fintech.
"""

from typing import Optional, Dict, Any

from .audit_repository import log_event

# Estos imports están aquí para futuras integraciones.
# No llamamos todavía a métodos concretos para no introducir errores
# mientras definimos la integración real con MangoPay.
from . import contract_engine  # type: ignore[attr-defined]
from . import wallet_service   # type: ignore[attr-defined]


class WalletOrchestrator:
    """
    Orquesta los eventos clave del flujo financiero:

    1) Depósito autorizado / retenido por la Fintech (por participante).
    2) Confirmación de que TODOS los depósitos del grupo son válidos.
    3) Pago al proveedor + distribución de comisiones (OÜ + sociedad española).
    4) Caso excepcional: proveedor no entrega → devolución SOLO del precio del producto
       al adjudicatario, sin gastos de gestión ni comisión.
    """

    # ============================================================
    # 1) Depósito individual autorizado por la Fintech
    # ============================================================
    def on_participant_deposit_authorized(
        self,
        session_id: str,
        participant_id: str,
        amount: float,
        fintech_operation_id: str,
        raw_payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        La Fintech (ej. MangoPay) confirma que el pago del participante
        ha sido autorizado y los fondos están retenidos en depósito condicional.

        Este evento NO significa aún que el grupo esté completo ni que la
        sesión sea válida; simplemente confirma que este participante está OK.
        """

        log_event(
            action="wallet_deposit_authorized",
            session_id=session_id,
            metadata={
                "participant_id": participant_id,
                "amount": amount,
                "fintech_operation_id": fintech_operation_id,
                "raw_payload": raw_payload or {},
            },
        )

        # Aquí, en una segunda fase, podremos:
        # - Actualizar un estado interno de "deposit_ok" por participante.
        # - Notificar al contract_engine que este participante está ok.
        #
        # Ejemplo futuro (no implementado para evitar errores):
        # contract_engine.on_deposit_authorized(session_id, participant_id, amount)

    # ============================================================
    # 2) Todos los depósitos del grupo están confirmados
    # ============================================================
    def on_all_deposits_confirmed(
        self,
        session_id: str,
        total_amount: float,
        fintech_batch_id: Optional[str] = None,
    ) -> None:
        """
        Se llama cuando la Fintech nos confirma que TODOS los depósitos
        del grupo comprador están correctamente retenidos y son válidos.

        Esto es la condición necesaria para:
        - Considerar la sesión plenamente válida a efectos de contratación.
        - Permitir que el motor determinista opere y adjudique.

        IMPORTANTE: aquí no se hace todavía el pago al proveedor,
        solo se confirma que el dinero del grupo está "on hold" correctamente.
        """

        log_event(
            action="wallet_all_deposits_confirmed",
            session_id=session_id,
            metadata={
                "total_amount": total_amount,
                "fintech_batch_id": fintech_batch_id,
            },
        )

        # En una fase posterior, aquí notificaremos al contract_engine que
        # la sesión tiene todos los depósitos OK y es apta para adjudicación.
        #
        # Ejemplo futuro:
        # contract_engine.on_all_deposits_confirmed(session_id, total_amount)

    # ============================================================
    # 3) Pago al proveedor del producto (caso normal)
    # ============================================================
    def on_supplier_invoice_ready(
        self,
        session_id: str,
        invoice_reference: str,
        product_price: float,
        mgmt_fee: float,
        commission_fee: float,
    ) -> None:
        """
        Flujo normal después de la adjudicación y del visto bueno de la OÜ:

        1) La OÜ valida el adjudicatario y la operación.
        2) La OÜ solicita la factura proforma al proveedor.
        3) El proveedor emite factura proforma → se registra invoice_reference.
        4) La OÜ remite a la Fintech la orden de pago al proveedor + reparto:
           - Precio producto → proveedor
           - Gastos de gestión → sociedad española (DMHG)
           - Comisión → OÜ estonia

        Este método representa el punto en el que el contrato dice:
        “paga al proveedor y distribuye las partidas”.
        """

        log_event(
            action="wallet_supplier_invoice_ready",
            session_id=session_id,
            metadata={
                "invoice_reference": invoice_reference,
                "product_price": product_price,
                "mgmt_fee": mgmt_fee,
                "commission_fee": commission_fee,
            },
        )

        # Aquí, en la integración real, llamaremos a wallet_service para:
        # - Ejecutar el pago al proveedor
        # - Enviar las partidas de gestión y comisión a las cuentas correspondientes
        #
        # Ejemplo futuro:
        # wallet_service.pay_supplier_and_distribute(
        #     session_id=session_id,
        #     invoice_reference=invoice_reference,
        #     product_price=product_price,
        #     mgmt_fee=mgmt_fee,
        #     commission_fee=commission_fee,
        # )

        # Y notificar al motor contractual:
        # contract_engine.on_supplier_paid(session_id, invoice_reference)

    # ============================================================
    # 4) CASO EXCEPCIONAL: proveedor no puede entregar el producto
    # ============================================================
    def on_force_majeure_supplier_failure(
        self,
        session_id: str,
        awardee_user_id: str,
        product_price: float,
        reason: str,
    ) -> None:
        """
        Caso excepcional previsto en el contrato:

        - El proveedor NO puede entregar el producto (fuerza mayor, cierre, etc.).
        - La OÜ decide activar la cláusula excepcional.
        - La Fintech debe devolver ÚNICAMENTE el precio del producto al adjudicatario,
          sin devolver comisión ni gastos de gestión.
        - El resto de participantes NO recibe ninguna devolución.

        Este método representa el “hook” operativo para ese escenario.
        """

        log_event(
            action="wallet_force_majeure_supplier_failure",
            session_id=session_id,
            metadata={
                "awardee_user_id": awardee_user_id,
                "product_price": product_price,
                "reason": reason,
            },
        )

        # En la integración real, aquí wallet_service ejecutaría:
        # - Transferir product_price al adjudicatario
        # - Cerrar la operación en la Fintech
        #
        # Ejemplo futuro:
        # wallet_service.refund_product_price_to_awardee(
        #     session_id=session_id,
        #     awardee_user_id=awardee_user_id,
        #     amount=product_price,
        # )
        #
        # Y el motor contractual marcaría la sesión como resuelta por fuerza mayor:
        # contract_engine.on_force_majeure_refund(
        #     session_id=session_id,
        #     awardee_user_id=awardee_user_id,
        #     product_price=product_price,
        #     reason=reason,
        # )


# Instancia global exportable
wallet_orchestrator = WalletOrchestrator()
