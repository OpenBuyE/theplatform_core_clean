"""
wallet_service.py
Puente lógico entre el motor contractual de Compra Abierta y la fintech (MangoPay u otra).

⚠️ IMPORTANTE (versión 1):
- Esta versión NO llama todavía a la API real de la fintech.
- NO escribe en Supabase ni en tablas nuevas.
- Solo define una interfaz clara y registra eventos en audit_logs.
- Así evitamos romper el backend mientras diseñamos la integración paso a paso.

La idea es:
- La fintech (MangoPay) lleva TODA la lógica de pagos reales (tarjetas, wallets, escrow).
- Compra Abierta solo:
    - Define el flujo contractual.
    - Recibe callbacks/notificaciones (webhooks) de la fintech.
    - Registra eventos de alto nivel para auditoría.

Este servicio define los puntos de entrada desde la fintech hacia tu motor:
- Depósito autorizado / confirmado para un participante.
- Depósito rechazado / fallido.
- Captura final de fondos al proveedor y reparto de comisiones.
- Caso excepcional de fuerza mayor (devolución parcial: solo precio de producto al adjudicatario).

En siguientes versiones:
- Aquí añadiremos llamadas HTTP reales hacia MangoPay.
- Y, si lo deseas, persistencia estructurada en Supabase (wallet_operations, etc.).
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime

from .audit_repository import log_event


class WalletService:
    """
    Capa de abstracción sobre la fintech.

    Su responsabilidad es puramente "orquestación contractual":
    - No decide adjudicatarios (eso es trabajo del adjudicator_engine).
    - No decide estados de sesión (eso es trabajo de session_engine / session_repository).
    - Solo asegura que el flujo de dinero real sigue lo que dice el Smart Contract.
    """

    # ============================================================
    #  1) DEPÓSITOS / PAGOS DE PARTICIPANTES
    # ============================================================
    def notify_deposit_authorized(
        self,
        *,
        session_id: str,
        participant_id: str,
        amount: float,
        currency: str,
        fintech_operation_id: str,
        raw_payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Llamada cuando la FINTECH nos confirma que:
        - la tarjeta del participante ha sido autorizada / el dinero está bloqueado en depósito,
        - pero aún no se ha "capturado" y enviado al proveedor.

        Esto normalmente llegará vía webhook desde MangoPay u otra fintech.

        Aquí NO hacemos lógica de negocio fuerte (no cambiamos estados de sesión),
        solo registramos el hecho y dejamos que el motor superior tome decisiones.
        """
        log_event(
            action="wallet_deposit_authorized",
            session_id=session_id,
            metadata={
                "participant_id": participant_id,
                "amount": amount,
                "currency": currency,
                "fintech_operation_id": fintech_operation_id,
                "raw_payload": raw_payload or {},
                "at": datetime.utcnow().isoformat(),
            },
        )

    def notify_deposit_failed(
        self,
        *,
        session_id: str,
        participant_id: str,
        amount: float,
        currency: str,
        fintech_operation_id: str,
        raw_payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Llamada cuando la FINTECH comunica que el intento de pago:
        - ha sido rechazado,
        - o no puede mantenerse el depósito,
        - o ha caducado / ha sido cancelado.

        Esto es crítico para tu regla de "grupo NO válido si algún depósito deja de ser válido",
        porque aunque se haya llenado el aforo lógico, el grupo financiero ya no es completo.
        """
        log_event(
            action="wallet_deposit_failed",
            session_id=session_id,
            metadata={
                "participant_id": participant_id,
                "amount": amount,
                "currency": currency,
                "fintech_operation_id": fintech_operation_id,
                "raw_payload": raw_payload or {},
                "at": datetime.utcnow().isoformat(),
            },
        )

    # ============================================================
    #  2) COMPROBAR QUE EL GRUPO ESTÁ FINANCIERAMENTE COMPLETO
    # ============================================================
    def can_session_be_financially_confirmed(
        self,
        *,
        session_id: str,
        expected_pax: int,
        confirmed_deposits: int,
    ) -> bool:
        """
        Criterio simple de "grupo financiero completo":

        - expected_pax = capacidad/aforo obligatorio de la sesión (capacity).
        - confirmed_deposits = número de participantes cuyo pago ha sido confirmado/autorizado
          por la fintech.

        Esta función no consulta BD ni la API de pagos: es un helper lógico puro.
        En el futuro:
        - podremos envolver aquí la lógica más compleja (por ejemplo:
          distintos estados en MangoPay, multi-método, etc.).
        """
       _full = confirmed_deposits >= expected_pax

        log_event(
            action="wallet_group_funding_check",
            session_id=session_id,
            metadata={
                "expected_pax": expected_pax,
                "confirmed_deposits": confirmed_deposits,
                "is_fully_funded": _full,
                "at": datetime.utcnow().isoformat(),
            },
        )

        return _full

    # ============================================================
    #  3) UNA VEZ ADJUDICADA LA SESIÓN (CASO NORMAL)
    # ============================================================
    def on_session_adjudicated(
        self,
        *,
        session_id: str,
        adjudicatario_id: str,
        product_amount: float,
        management_fee_amount: float,
        commission_fee_amount: float,
        currency: str,
        fintech_session_wallet_id: Optional[str] = None,
        raw_payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Llamada por el motor contractual cuando:

        - La sesión ya ha sido adjudicada (hay adjudicatario determinista).
        - El grupo financiero está completo (todos depósitos OK).
        - Toca la parte financiera:
            1) La fintech captura los fondos del grupo.
            2) Paga al proveedor el precio del producto.
            3) Distribuye management_fee + comisión a:
                - sociedad española (gastos de gestión)
                - OÜ estonia (comisión de la plataforma).

        Esta versión 1 NO llama a la API real de la fintech, solo registra el evento
        y la intención, para que podamos trazar el flujo end-to-end.

        Más adelante:
        - Aquí se integrará la llamada HTTP/SDK hacia MangoPay (u otra).
        """
        log_event(
            action="wallet_on_session_adjudicated",
            session_id=session_id,
            metadata={
                "adjudicatario_id": adjudicatario_id,
                "product_amount": product_amount,
                "management_fee_amount": management_fee_amount,
                "commission_fee_amount": commission_fee_amount,
                "currency": currency,
                "fintech_session_wallet_id": fintech_session_wallet_id,
                "raw_payload": raw_payload or {},
                "at": datetime.utcnow().isoformat(),
            },
        )

    # ============================================================
    #  4) CASO EXCEPCIONAL — DEVOLUCIÓN SOLO DEL PRECIO DEL PRODUCTO
    # ============================================================
    def on_force_majeure_product_not_deliverable(
        self,
        *,
        session_id: str,
        adjudicatario_id: str,
        product_amount: float,
        currency: str,
        fintech_operation_id: Optional[str] = None,
        reason: str = "force_majeure",
        raw_payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Caso excepcional descrito en el contrato:

        - El proveedor NO puede entregar el producto (rotura de stock irreversible, cierre, etc.).
        - No es culpa del adjudicatario ni de la plataforma.
        - La solución jurídica es: la fintech devuelve SOLO el importe del precio del producto
          al adjudicatario final, NO los gastos de gestión ni la comisión.

        Flujo conceptual:
        - La OÜ notifica a la fintech que debe devolverse el importe product_amount al adjudicatario.
        - La fintech ejecuta la devolución según sus reglas (refund, payout, etc.).
        - El contrato sigue vigente en cuanto a comisiones y gastos de gestión (no se devuelven).

        Esta versión 1 solo registra el evento.
        """
        log_event(
            action="wallet_force_majeure_refund_product_only",
            session_id=session_id,
            metadata={
                "adjudicatario_id": adjudicatario_id,
                "product_amount": product_amount,
                "currency": currency,
                "reason": reason,
                "fintech_operation_id": fintech_operation_id,
                "raw_payload": raw_payload or {},
                "at": datetime.utcnow().isoformat(),
            },
        )

    # ============================================================
    #  5) PLACEHOLDERS PARA LA INTEGRACIÓN REAL CON MANGOPAY
    # ============================================================
    #
    # Estos métodos internos serán rellenados cuando definamos:
    # - si usamos SDK oficial de MangoPay o HTTP puro,
    # - cómo mapeamos "session_id" y "participant_id" a "wallet_id", "card_id", etc.
    #
    # Nota: de momento no se llaman desde ningún sitio, por lo que NO causan errores.
    #

    def _create_fintech_session_wallet(self, *, session_id: str) -> str:
        """
        Crear o recuperar una wallet específica de la sesión en la fintech.
        (placeholder — implementación futura)
        """
        # TODO: implementar integración real con fintech (MangoPay u otra)
        wallet_id = f"FINTECH-WALLET-{session_id}"
        log_event(
            action="wallet_placeholder_create_fintech_session_wallet",
            session_id=session_id,
            metadata={"wallet_id": wallet_id},
        )
        return wallet_id

    def _call_fintech_capture_group_funds(
        self,
        *,
        session_id: str,
        fintech_session_wallet_id: str,
        total_amount: float,
        currency: str,
    ) -> None:
        """
        Orden de captura de fondos del grupo en la fintech.
        (placeholder — implementación futura)
        """
        log_event(
            action="wallet_placeholder_capture_group_funds",
            session_id=session_id,
            metadata={
                "fintech_session_wallet_id": fintech_session_wallet_id,
                "total_amount": total_amount,
                "currency": currency,
            },
        )

    def _call_fintech_refund_product_amount(
        self,
        *,
        session_id: str,
        adjudicatario_id: str,
        product_amount: float,
        currency: str,
    ) -> None:
        """
        Orden de devolución del precio del producto al adjudicatario en caso de fuerza mayor.
        (placeholder — implementación futura)
        """
        log_event(
            action="wallet_placeholder_refund_product_amount",
            session_id=session_id,
            metadata={
                "adjudicatario_id": adjudicatario_id,
                "product_amount": product_amount,
                "currency": currency,
            },
        )


# Instancia global exportable
wallet_service = WalletService()
