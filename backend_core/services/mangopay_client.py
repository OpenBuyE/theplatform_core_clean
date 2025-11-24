# backend_core/services/mangopay_client.py

import os
import requests
from typing import Optional, Dict, Any

# --------------------------------------------------------
# Config MangoPay desde variables de entorno
# --------------------------------------------------------

MGP_BASE = "https://api.mangopay.com/v2.01"
MGP_CLIENT_ID = os.getenv("MANGOPAY_CLIENT_ID", "")
MGP_API_KEY = os.getenv("MANGOPAY_API_KEY", "")
MGP_ENV = os.getenv("MANGOPAY_ENV", "sandbox")  # sandbox | production


def _headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
    }


def _auth() -> (str, str):
    return (MGP_CLIENT_ID, MGP_API_KEY)


# ========================================================
# 1) Crear Legal User (operador)
# ========================================================

def create_legal_user(
    name: str,
    legal_person_type: str,
    email: str,
    headquarters_address: Dict[str, Any],
    legal_representative: Dict[str, Any],
    country: str,
) -> Dict[str, Any]:

    url = f"{MGP_BASE}/{MGP_CLIENT_ID}/users/legal"

    payload = {
        "Name": name,
        "LegalPersonType": legal_person_type,
        "Email": email,
        "HeadquartersAddress": headquarters_address,
        "LegalRepresentativeFirstName": legal_representative["first_name"],
        "LegalRepresentativeLastName": legal_representative["last_name"],
        "LegalRepresentativeEmail": legal_representative["email"],
        "LegalRepresentativeBirthday": legal_representative["birthday"],
        "LegalRepresentativeNationality": legal_representative["nationality"],
        "LegalRepresentativeCountryOfResidence": legal_representative["residence"],
        "Tag": "operator_onboarding",
    }

    resp = requests.post(url, json=payload, headers=_headers(), auth=_auth())
    resp.raise_for_status()
    return resp.json()


# ========================================================
# 2) Crear Wallet del operador
# ========================================================

def create_wallet_for_operator(
    mango_user_id: str,
    currency: str = "EUR",
) -> Dict[str, Any]:

    url = f"{MGP_BASE}/{MGP_CLIENT_ID}/wallets"

    payload = {
        "Owners": [mango_user_id],
        "Description": "Operator Primary Wallet",
        "Currency": currency,
        "Tag": "operator_wallet",
    }

    resp = requests.post(url, json=payload, headers=_headers(), auth=_auth())
    resp.raise_for_status()
    return resp.json()


# ========================================================
# 3) Crear documento KYC
# ========================================================

def create_kyc_document(
    mango_user_id: str,
    doc_type: str = "IDENTITY_PROOF",
) -> Dict[str, Any]:

    url = f"{MGP_BASE}/{MGP_CLIENT_ID}/users/{mango_user_id}/KYC/documents"

    payload = {
        "Type": doc_type,
        "Tag": "operator_kyc",
    }

    resp = requests.post(url, json=payload, headers=_headers(), auth=_auth())
    resp.raise_for_status()
    return resp.json()


# ========================================================
# 4) Subir páginas de documento KYC
# ========================================================

def upload_kyc_document_page(
    mango_user_id: str,
    kyc_doc_id: str,
    file_content: bytes,
) -> Dict[str, Any]:

    url = f"{MGP_BASE}/{MGP_CLIENT_ID}/users/{mango_user_id}/KYC/documents/{kyc_doc_id}/pages"

    headers = {
        "Content-Type": "application/octet-stream",
    }

    resp = requests.post(url, data=file_content, headers=headers, auth=_auth())
    resp.raise_for_status()
    return resp.json()


# ========================================================
# 5) Enviar documento para validación
# ========================================================

def submit_kyc_document(
    mango_user_id: str,
    kyc_doc_id: str,
) -> Dict[str, Any]:

    url = f"{MGP_BASE}/{MGP_CLIENT_ID}/users/{mango_user_id}/KYC/documents/{kyc_doc_id}"

    payload = {"Status": "VALIDATION_ASKED"}

    resp = requests.put(url, json=payload, headers=_headers(), auth=_auth())
    resp.raise_for_status()
    return resp.json()


# ========================================================
# 6) Consultar estado KYC
# ========================================================

def get_kyc_document(
    mango_user_id: str,
    kyc_doc_id: str,
) -> Dict[str, Any]:

    url = f"{MGP_BASE}/{MGP_CLIENT_ID}/users/{mango_user_id}/KYC/documents/{kyc_doc_id}"

    resp = requests.get(url, headers=_headers(), auth=_auth())
    resp.raise_for_status()
    return resp.json()


# ========================================================
# 7) Consultar usuario legal (estado KYC global)
# ========================================================

def get_legal_user(
    mango_user_id: str
) -> Dict[str, Any]:

    url = f"{MGP_BASE}/{MGP_CLIENT_ID}/users/legal/{mango_user_id}"

    resp = requests.get(url, headers=_headers(), auth=_auth())
    resp.raise_for_status()
    return resp.json()
