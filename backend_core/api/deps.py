# backend_core/api/deps.py
from __future__ import annotations

from functools import lru_cache

from backend_core.services.audit_repository import AuditRepository
from backend_core.services.wallet_orchestrator import WalletOrchestrator


@lru_cache(maxsize=1)
def get_audit_repo() -> AuditRepository:
    """
    Repositorio de auditoría singleton (a nivel de proceso).
    """
    return AuditRepository()


@lru_cache(maxsize=1)
def get_wallet_orchestrator() -> WalletOrchestrator:
    """
    Orquestador de wallet singleton, reutilizando el mismo AuditRepository.
    """
    audit_repo = get_audit_repo()
    return WalletOrchestrator(audit_repo=audit_repo)
