"""
audit_repository.py
Repositorio de auditoría estructurada para Compra Abierta.

Este módulo registra:
- Adjudicaciones
- Expiraciones
- Activación de sesiones
- Cambios de seeds
- Eventos del motor (warnings, skips, info)
- Actividad del panel (en caso necesario)

La tabla recomendada en Supabase es:

    public.audit_logs (
        id uuid primary key default gen_random_uuid(),
        action text,
        session_id uuid null,
        user_id uuid null,
        organization_id uuid null,
        metadata jsonb,
        created_at timestamptz default now()
    )

"""

from datetime import datetime
from typing import Optional, Dict, Any
from .supabase_client import supabase


AUDIT_TABLE = "audit_logs"


class AuditRepository:

    # ---------------------------------------------------------
    #  REGISTRO DE EVENTOS (FUNCIÓN CENTRAL)
    # ---------------------------------------------------------
    def log_event(
        self,
        action: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Inserta un evento de auditoría en la tabla audit_logs.
        Siempre registra created_at automáticamente.
        """

        if metadata is None:
            metadata = {}

        supabase.table(AUDIT_TABLE).insert({
            "action": action,
            "session_id": session_id,
            "user_id": user_id,
            "organization_id": organization_id,
            "metadata": metadata
        }).execute()

    # ---------------------------------------------------------
    #  OBTENER LOGS (para panel de admin)
    # ---------------------------------------------------------
    def get_logs(self, limit: int = 2000):
        response = (
            supabase
            .table(AUDIT_TABLE)
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    # ---------------------------------------------------------
    #  FILTRAR LOGS POR SESIÓN
    # ---------------------------------------------------------
    def get_logs_by_session(self, session_id: str, limit: int = 500):
        response = (
            supabase
            .table(AUDIT_TABLE)
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []


# Instancia exportable
audit_repository = AuditRepository()


# helper global — evita imports circulares en los servicios
def log_event(
    action: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    audit_repository.log_event(
        action=action,
        session_id=session_id,
        user_id=user_id,
        organization_id=organization_id,
        metadata=metadata
    )
