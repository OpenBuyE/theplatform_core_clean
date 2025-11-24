# backend_core/services/kpi_repository.py

from datetime import date, datetime
from typing import Dict, List

from backend_core.services.supabase_client import table


# ======================================================
#  BLOQUE 1 — KPIs BÁSICOS (sesiones y eventos wallet)
#  (Compatibles con las versiones anteriores)
# ======================================================

def kpi_sessions_active() -> int:
    """
    Número total de sesiones con status = 'active'
    """
    resp = (
        table("ca_sessions")
        .select("id")
        .eq("status", "active")
        .execute()
    )
    return len(resp.data or [])


def kpi_sessions_finished() -> int:
    """
    Número total de sesiones con status = 'finished'
    """
    resp = (
        table("ca_sessions")
        .select("id")
        .eq("status", "finished")
        .execute()
    )
    return len(resp.data or [])


def kpi_wallet_deposit_ok() -> int:
    """
    Número de eventos wallet_deposit_ok registrados en ca_audit_logs
    """
    resp = (
        table("ca_audit_logs")
        .select("id")
        .eq("action", "wallet_deposit_ok")
        .execute()
    )
    return len(resp.data or [])


def kpi_wallet_settlement_completed() -> int:
    """
    Número de eventos wallet_settlement_completed registrados en ca_audit_logs
    """
    resp = (
        table("ca_audit_logs")
        .select("id")
        .eq("action", "wallet_settlement_completed")
        .execute()
    )
    return len(resp.data or [])


def kpi_wallet_force_majeure() -> int:
    """
    Número de eventos wallet_force_majeure_refund registrados en ca_audit_logs
    """
    resp = (
        table("ca_audit_logs")
        .select("id")
        .eq("action", "wallet_force_majeure_refund")
        .execute()
    )
    return len(resp.data or [])


def kpi_sessions_by_module() -> Dict[str, int]:
    """
    Devuelve un dict {module_id: número_de_sesiones_asignadas}
    basado en ca_session_modules.
    """
    resp = (
        table("ca_session_modules")
        .select("module_id")
        .execute()
    )
    rows = resp.data or []

    stats: Dict[str, int] = {}
    for r in rows:
        m = r.get("module_id")
        if not m:
            continue
        stats[m] = stats.get(m, 0) + 1

    return stats


def kpi_audit_events_by_day() -> Dict[str, int]:
    """
    Devuelve un dict {YYYY-MM-DD: numero_eventos} agrupado por día
    a partir de ca_audit_logs.created_at.
    """
    resp = (
        table("ca_audit_logs")
        .select("created_at")
        .execute()
    )
    rows = resp.data or []

    stats: Dict[str, int] = {}
    for r in rows:
        created_at = r.get("created_at")
        if not created_at:
            continue
        # created_at esperado en ISO8601, cogemos solo la parte de fecha
        day = str(created_at).split("T")[0]
        stats[day] = stats.get(day, 0) + 1

    return stats


def kpi_sessions_status_distribution() -> Dict[str, int]:
    """
    Devuelve un dict {status: count} para todas las sesiones.
    """
    resp = (
        table("ca_sessions")
        .select("status")
        .execute()
    )
    rows = resp.data or []

    stats: Dict[str, int] = {}
    for r in rows:
        status = r.get("status")
        if not status:
            continue
        stats[status] = stats.get(status, 0) + 1

    return stats


# ======================================================
#  BLOQUE 2 — INTERFAZ PRO PARA OPERATOR DASHBOARD PRO
#  (Nombres usados en operator_dashboard_pro.py)
# ======================================================

def kpi_count_active() -> int:
    """
    Alias PRO de kpi_sessions_active()
    """
    return kpi_sessions_active()


def kpi_count_finished() -> int:
    """
    Alias PRO de kpi_sessions_finished()
    """
    return kpi_sessions_finished()


def kpi_sum_deposits() -> float:
    """
    Suma de importes de depósitos (EUROS) basada en ca_audit_logs.

    Supone que en metadata existe una clave 'amount' con el importe numérico
    de cada evento wallet_deposit_ok.

    Si no existe o no es convertible a float, se ignora silenciosamente.
    """
    resp = (
        table("ca_audit_logs")
        .select("action, metadata")
        .eq("action", "wallet_deposit_ok")
        .execute()
    )
    rows = resp.data or []

    total = 0.0
    for r in rows:
        metadata = r.get("metadata") or {}
        amount = metadata.get("amount")
        if amount is None:
            continue
        try:
            total += float(amount)
        except (TypeError, ValueError):
            continue

    return total


def _parse_day_from_iso(iso_str: str) -> date | None:
    """
    Convierte un string ISO8601 en date (YYYY-MM-DD).
    Si falla, devuelve None.
    """
    if not iso_str:
        return None
    try:
        # Caso típico: '2025-11-24T10:35:21.602+00:00'
        # Nos quedamos solo con la parte de fecha
        day_str = str(iso_str).split("T")[0]
        return datetime.strptime(day_str, "%Y-%m-%d").date()
    except Exception:
        return None


def kpi_timeseries_active(start: date, end: date) -> List[Dict[str, object]]:
    """
    Devuelve una lista de dicts [{day: date, count: int}, ...]
    con el número de sesiones activadas por día en el rango [start, end].

    Usa ca_sessions.activated_at.
    """
    resp = (
        table("ca_sessions")
        .select("activated_at")
        .execute()
    )
    rows = resp.data or []

    # Inicializamos todos los días del rango con 0
    current = start
    stats: Dict[date, int] = {}
    while current <= end:
        stats[current] = 0
        current += timedelta(days=1)  # type: ignore[name-defined]

    # Contabilizar sesiones activadas
    from datetime import timedelta as _timedelta  # para evitar confusión de nombre
    current = start
    stats = {}
    while current <= end:
        stats[current] = 0
        current += _timedelta(days=1)

    for r in rows:
        activated_at = r.get("activated_at")
        d = _parse_day_from_iso(activated_at)
        if d is None:
            continue
        if d < start or d > end:
            continue
        stats[d] = stats.get(d, 0) + 1

    # Convertimos a lista ordenada para plotly
    result: List[Dict[str, object]] = []
    for day in sorted(stats.keys()):
        result.append({"day": day, "count": stats[day]})

    return result


def kpi_timeseries_deposits(start: date, end: date) -> List[Dict[str, object]]:
    """
    Devuelve una lista de dicts [{day: date, amount: float}, ...]
    con el total de depósitos por día en el rango [start, end].

    Usa ca_audit_logs con action = 'wallet_deposit_ok' y metadata.amount.
    """
    resp = (
        table("ca_audit_logs")
        .select("action, created_at, metadata")
        .eq("action", "wallet_deposit_ok")
        .execute()
    )
    rows = resp.data or []

    from datetime import timedelta as _timedelta

    # Inicializamos todos los días del rango con 0
    current = start
    stats: Dict[date, float] = {}
    while current <= end:
        stats[current] = 0.0
        current += _timedelta(days=1)

    for r in rows:
        created_at = r.get("created_at")
        d = _parse_day_from_iso(created_at)
        if d is None:
            continue
        if d < start or d > end:
            continue

        metadata = r.get("metadata") or {}
        amount = metadata.get("amount")
        if amount is None:
            continue
        try:
            val = float(amount)
        except (TypeError, ValueError):
            continue

        stats[d] = stats.get(d, 0.0) + val

    result: List[Dict[str, object]] = []
    for day in sorted(stats.keys()):
        result.append({"day": day, "amount": stats[day]})

    return result

