"""
mangopay_client.py
Cliente HTTP de bajo nivel para MangoPay.

Este módulo NO contiene lógica de negocio, solo:
- Construcción de URLs
- Autenticación básica (client_id + api_key)
- Métodos GET / POST genéricos

⚠️ IMPORTANTE:
- Los endpoints y payloads exactos de MangoPay deben verificarse
  con la documentación oficial antes de usar en producción.
"""

import os
import requests
from typing import Any, Dict, Optional


class MangoPayClient:
    def __init__(
        self,
        client_id: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        # Credenciales desde entorno
        self.client_id = client_id or os.getenv("MANGOPAY_CLIENT_ID")
        self.api_key = api_key or os.getenv("MANGOPAY_API_KEY")

        if not self.client_id or not self.api_key:
            raise RuntimeError(
                "MangoPayClient: faltan MANGOPAY_CLIENT_ID o MANGOPAY_API_KEY en el entorno."
            )

        # URL base por defecto v2.01
        self.base_url = base_url or os.getenv(
            "MANGOPAY_API_BASE",
            "https://api.mangopay.com/v2.01",
        ).rstrip("/")

    # -----------------------------------------------------
    #  Helpers internos
    # -----------------------------------------------------
    def _build_url(self, path: str) -> str:
        """
        Construye la URL completa:
        base_url / {client_id} / path
        """
        path = path.lstrip("/")
        return f"{self.base_url}/{self.client_id}/{path}"

    def _auth(self):
        """
        Autenticación básica HTTP.
        MangoPay suele usar (client_id, api_key) como Basic Auth.
        """
        return (self.client_id, self.api_key)

    # -----------------------------------------------------
    #  Métodos públicos
    # -----------------------------------------------------
    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = self._build_url(path)
        resp = requests.get(url, params=params, auth=self._auth())

        if not resp.ok:
            raise RuntimeError(
                f"MangoPay GET error [{resp.status_code}] {resp.text}"
            )

        return resp.json()

    def post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = self._build_url(path)
        resp = requests.post(url, json=payload, auth=self._auth())

        if not resp.ok:
            raise RuntimeError(
                f"MangoPay POST error [{resp.status_code}] {resp.text}"
            )

        return resp.json()


# Instancia global reutilizable
mangopay_client = MangoPayClient()
