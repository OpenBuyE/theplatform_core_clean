"""
mangopay_adapter.py
Adaptador MangoPay para la capa wallet / fintech.

Rol:
- Traducir operaciones de dominio (depósito, liberación, pago a proveedor)
  a llamadas concretas contra la API de MangoPay.
- Centralizar aquí todo lo específico de MangoPay para que el resto
  del backend (wallet_orchestrator, contract_engine, API REST)
  no dependan de detalles de implementación.

⚠️ ESTADO ACTUAL:
- Es un esqueleto híbrido: preparado para MangoPay pero con varios
  métodos en modo "TODO" que habrá que ajustar con los endpoints reales.
"""

from typing import Any, Dict, Optional

from .mangopay_client import mangopay_client
from .audit_repository import log_event


class MangoPayWalletAdapter:
    """
    Adaptador de alto nivel para operaciones típicas:

    - registrar usuario (si fuera necesario en MangoPay)
    - crear wallet para el usuario/grupo
    - registrar tarjeta / medio de pago
    - crear payin (depósito) hacia wallet de sesión
    - consultar estado del payin
    - crear payout (pago) hacia proveedor / merchant
    """

    # -----------------------------------------------------
    #  Usuarios / Wallets
    # -----------------------------------------------------
    def create_natural_user(self, user_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un usuario 'natural' en MangoPay.

        user_payload deberá adaptarse a lo requerido por MangoPay:
        {
            "FirstName": "...",
            "LastName": "...",
            "Email": "...",
            ...
        }
        """
        # TODO: adaptar a /users/natural de MangoPay real
        result = mangopay_client.post("/users/natural", user_payload)

        log_event(
            action="mangopay_user_created",
            metadata={"response": result},
        )
        return result

    def create_wallet_for_user(self, user_id: str, currency: str = "EUR") -> Dict[str, Any]:
        """
        Crea un wallet para un usuario en MangoPay.
        Este wallet podría asociarse a:
        - un usuario participante
        - o un wallet de sesión/grupo (si se modela así)
        """
        payload = {
            "Owners": [user_id],
            "Description": "Wallet CompraAbierta",
            "Currency": currency,
        }

        # TODO: revisar endpoint exacto para wallets
        result = mangopay_client.post("/wallets", payload)

        log_event(
            action="mangopay_wallet_created",
            metadata={"user_id": user_id, "response": result},
        )
        return result

    # -----------------------------------------------------
    #  Payins (depósitos hacia el wallet custodia)
    # -----------------------------------------------------
    def create_card_payin_to_wallet(
        self,
        author_id: str,
        credited_wallet_id: str,
        amount_cents: int,
        currency: str,
        session_id: str,
        participant_id: str,
    ) -> Dict[str, Any]:
        """
        Crea un payin mediante tarjeta hacia el wallet de sesión.

        amount_cents: en céntimos, p.ej. 30€ → 3000
        """

        payload = {
            # TODO: adaptar completamente según MangoPay:
            "AuthorId": author_id,
            "CreditedWalletId": credited_wallet_id,
            "DebitedFunds": {
                "Currency": currency,
                "Amount": amount_cents,
            },
            "Fees": {
                "Currency": currency,
                "Amount": 0,
            },
            # Campos de metadatos para traza interna
            "Tag": f"session={session_id};participant={participant_id}",
            # Tipo/referencia de pago (placeholder)
            "PaymentType": "CARD",
            "ExecutionType": "DIRECT",
        }

        result = mangopay_client.post("/payins/card/direct", payload)

        log_event(
            action="mangopay_payin_created",
            metadata={
                "session_id": session_id,
                "participant_id": participant_id,
                "author_id": author_id,
                "wallet_id": credited_wallet_id,
                "amount_cents": amount_cents,
                "response": result,
            },
        )
        return result

    def get_payin(self, payin_id: str) -> Dict[str, Any]:
        """
        Consulta el estado de un payin concreto.
        """
        result = mangopay_client.get(f"/payins/{payin_id}")

        log_event(
            action="mangopay_payin_fetched",
            metadata={"payin_id": payin_id, "response": result},
        )
        return result

    # -----------------------------------------------------
    #  Payouts (pago al proveedor / merchant)
    # -----------------------------------------------------
    def create_payout_to_bank_account(
        self,
        author_id: str,
        debited_wallet_id: str,
        bank_account_id: str,
        amount_cents: int,
        currency: str,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        Crea un payout desde el wallet de sesión hacia una cuenta bancaria
        del proveedor (o merchant). La estructura exacta depende del modelo
        de MangoPay (bank accounts, legal users, etc.).
        """

        payload = {
            # TODO: adaptar al endpoint real de payouts de MangoPay
            "AuthorId": author_id,
            "DebitedWalletId": debited_wallet_id,
            "DebitedFunds": {
                "Currency": currency,
                "Amount": amount_cents,
            },
            "Fees": {
                "Currency": currency,
                "Amount": 0,
            },
            "BankAccountId": bank_account_id,
            "Tag": f"session={session_id};payout=provider",
            "PayoutModeRequested": "STANDARD",
        }

        result = mangopay_client.post("/payouts/bankwire", payload)

        log_event(
            action="mangopay_payout_created",
            metadata={
                "session_id": session_id,
                "wallet_id": debited_wallet_id,
                "bank_account_id": bank_account_id,
                "amount_cents": amount_cents,
                "response": result,
            },
        )
        return result


# Instancia global
mangopay_adapter = MangoPayWalletAdapter()
