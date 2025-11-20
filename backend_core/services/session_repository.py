import streamlit as st

from backend_core.services.supabase_client import fetch_rows, update_row
from backend_core.services.audit_repository import log_action
from backend_core.services.context import (
    get_current_user,
    get_current_org,
    get_current_permissions,
)


def _require_org_or_empty() -> str | None:
    """
    Devuelve organization_id si existe.
    Si no, muestra advertencia y devuelve None → las funciones devuelven [].
    """
    org_id = get_current_org()
    if not org_id:
        st.warning("Selecciona una organización para continuar.")
        return None
    return org_id


# -------------------------------------------------
#   PARQUE / SESIONES ACTIVAS / CADENAS (EXISTENTE)
# -------------------------------------------------

def get_sessions() -> list[dict]:
    """
    Sesiones en estado 'parked' de la organización activa.
    Esto corresponde al Parque de Sesiones.
    """
    org_id = _require_org_or_empty()
    if not org_id:
        return []

    params = {
        "select": "*",
        "status": "eq.parked",
        "organization_id": f"eq.{org_id}",
    }
    return fetch_rows("sessions", params)


def get_active_sessions() -> list[dict]:
    """
    Sesiones activas (active, open, running) de la organización activa.
    """
    org_id = _require_org_or_empty()
    if not org_id:
        return []

    params = {
        "select": "*",
        "status": "in.(active,open,running)",
        "organization_id": f"eq.{org_id}",
    }
    return fetch_rows("sessions", params)


def get_chains() -> list[dict]:
    """
    Sesiones con cadena operativa (chain_group_id no nulo)
    de la organización activa.
    """
    org_id = _require_org_or_empty()
    if not org_id:
        return []

    params = {
        "select": "*",
        "chain_group_id": "not.is.null",
        "organization_id": f"eq.{org_id}",
    }
    return fetch_rows("sessions", params)


def activate_session(session_id: str) -> dict:
    """
    Cambia una sesión a estado 'active', la liga a la organización activa
    y registra auditoría.

    Requiere:
      - organización activa
      - usuario activo
      - permiso 'session.activate'
    """
    org_id = get_current_org()
    user_id = get_current_user()

    if not org_id:
        raise RuntimeError("No hay organización activa.")
    if not user_id:
        raise RuntimeError("No hay usuario activo.")
    if "session.activate" not in get_current_permissions():
        raise RuntimeError("No tienes permisos para activar sesiones.")

    patch = {
        "status": "active",
        "organization_id": org_id,
    }

    updated = update_row("sessions", session_id, patch)

    if updated is None:
        raise RuntimeError("No se pudo actualizar la sesión en Supabase.")

    # Registro de auditoría
    log_action(
        action="activate_session",
        session_id=session_id,
        performed_by=user_id,
        metadata={"new_status": "active"},
    )

    return updated


# -------------------------------------------------
#   NUEVAS FUNCIONES: PROGRAMADAS / STANDBY / SERIES
# -------------------------------------------------

def get_scheduled_sessions() -> list[dict]:
    """
    Sesiones programadas (futuras), típicamente:
      - status = 'scheduled'
      - start_at en el futuro
    de la organización activa.

    Esto corresponde al tipo B que comentabas:
    sesiones que saldrán al frontend en una fecha futura.
    """
    org_id = _require_org_or_empty()
    if not org_id:
        return []

    params = {
        "select": "*",
        "status": "eq.scheduled",
        "organization_id": f"eq.{org_id}",
        "order": "start_at.asc",
    }
    return fetch_rows("sessions", params)


def get_standby_sessions() -> list[dict]:
    """
    Sesiones en preparación / Stand by:

      - status = 'standby' (o 'draft', según definas)
      - start_at es nulo (no tienen fecha de salida aún)

    Esto corresponde al tipo C:
    sesiones preparadas para entrar en el ciclo de venta
    y que podrían aparecer en un apartado de "futuras sesiones".
    """
    org_id = _require_org_or_empty()
    if not org_id:
        return []

    params = {
        "select": "*",
        "status": "eq.standby",
        "organization_id": f"eq.{org_id}",
    }
    return fetch_rows("sessions", params)


def get_sessions_for_series(series_id: str) -> list[dict]:
    """
    Devuelve todas las sesiones asociadas a una serie concreta (session_series.id)
    de la organización activa, ordenadas por sequence_number.

    Esto permitirá manejar series tipo:
       X23.1, X23.2, X23.3...
    dentro de una misma organización.
    """
    org_id = _require_org_or_empty()
    if not org_id:
        return []

    if not series_id:
        st.error("Se ha solicitado sesiones de una serie, pero falta series_id.")
        return []

    params = {
        "select": "*",
        "organization_id": f"eq.{org_id}",
        "series_id": f"eq.{series_id}",
        "order": "sequence_number.asc",
    }
    return fetch_rows("sessions", params)



