import typing as t
from backend_core.services.supabase_client import table
from backend_core.services.operator_repository import (
    get_operator_allowed_countries,
    ensure_country_filter,
)

# =========================================================
# HELPERS INTERNOS
# =========================================================

def _safe_data(resp):
    """Compatibilidad con diferentes formatos del wrapper REST."""
    if hasattr(resp, "data"):
        return resp.data
    return resp.get("data")


# =========================================================
# MODULES — CRUD + MULTIPAÍS + BATCHES
# =========================================================

def list_all_modules(operator_id: str) -> t.List[dict]:
    """
    Lista todos los módulos accesibles para el operador.
    Filtra automáticamente por país.
    """
    allowed = get_operator_allowed_countries(operator_id)

    qb = table("ca_modules").select("*")
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_data(resp) or []


def get_module_by_id(module_id: str) -> t.Optional[dict]:
    """
    Devuelve un módulo por ID (detalle directo, sin filtro).
    """
    resp = (
        table("ca_modules")
        .select("*")
        .eq("id", module_id)
        .single()
        .execute()
    )
    return _safe_data(resp)


# =========================================================
# MODULE BATCH CREATION
# =========================================================

def create_modules_batch(
    product_id: str,
    batch_size: int,
    country_code: str,
    module_code_prefix: str = "MOD",
) -> t.List[dict]:
    """
    Crea un batch de módulos para un mismo producto.
    Todos los módulos se crean con:
        - product_id
        - country_code
        - module_code = PREFIX + incremental
        - is_active = True
        - is_assigned = False
    """
    module_rows = []

    for i in range(batch_size):
        module_rows.append({
            "product_id": product_id,
            "country_code": country_code,
            "is_active": True,
            "is_assigned": False,
            "module_code": f"{module_code_prefix}-{i+1}",
        })

    resp = table("ca_modules").insert(module_rows).execute()
    return _safe_data(resp) or []


# =========================================================
# ASSIGN MODULE TO SESSION
# =========================================================

def assign_module(session_id: str, module_id: str) -> dict:
    """
    Asigna un módulo a una sesión:
        - marca módulo como is_assigned=True
        - crea registro en ca_session_modules
    """
    # 1. Marcar módulo como asignado
    table("ca_modules").update(
        {"is_assigned": True}
    ).eq("id", module_id).execute()

    # 2. Crear vínculo en tabla relacional
    resp = table("ca_session_modules").insert({
        "session_id": session_id,
        "module_id": module_id
    }).execute()

    return _safe_data(resp)


def get_module_for_session(session_id: str) -> t.Optional[dict]:
    """
    Devuelve el módulo asociado a una sesión.
    """
    resp = (
        table("ca_session_modules")
        .select("module_id")
        .eq("session_id", session_id)
        .single()
        .execute()
    )

    link = _safe_data(resp)
    if not link:
        return None

    return get_module_by_id(link["module_id"])


# =========================================================
# MARKERS — STATES
# =========================================================

def mark_module_assigned(module_id: str) -> None:
    """
    Marca módulo como asignado (seguridad adicional).
    """
    table("ca_modules").update(
        {"is_assigned": True}
    ).eq("id", module_id).execute()


def mark_module_awarded(module_id: str) -> None:
    """
    Marca módulo como adjudicado.
    """
    table("ca_modules").update(
        {"is_awarded": True}
    ).eq("id", module_id).execute()


# =========================================================
# MODULES AVAILABLE FOR PRODUCT
# =========================================================

def get_available_modules_for_product(
    product_id: str,
    operator_id: str,
) -> t.List[dict]:
    """
    Lista solo los módulos NO asignados, activos y del país adecuado.
    Útil para Product Creator Pro y Session Creator.
    """
    allowed = get_operator_allowed_countries(operator_id)

    qb = (
        table("ca_modules")
        .select("*")
        .eq("product_id", product_id)
        .eq("is_active", True)
        .eq("is_assigned", False)
    )

    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_data(resp) or []


# =========================================================
# BATCHES LOOKUP
# =========================================================

def list_batches(operator_id: str) -> t.List[dict]:
    """
    Lista todos los batches de módulos accesibles al operador.
    """
    allowed = get_operator_allowed_countries(operator_id)

    qb = table("ca_module_batches").select("*")
    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_data(resp) or []


def get_batch_modules(batch_id: str, operator_id: str) -> t.List[dict]:
    """
    Devuelve todos los módulos de un batch.
    """
    allowed = get_operator_allowed_countries(operator_id)

    qb = (
        table("ca_modules")
        .select("*")
        .eq("batch_id", batch_id)
    )

    qb = ensure_country_filter(qb, allowed)

    resp = qb.execute()
    return _safe_data(resp) or []
