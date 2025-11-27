# backend_core/services/product_repository_v2.py

from datetime import datetime
from backend_core.services.supabase_client import table
from backend_core.services.operator_repository import ensure_country_filter


# ============================================================
# LISTAR PRODUCTOS (V2)
# ============================================================

def list_products_v2(operator=None):
    """
    Lista productos con filtro multi-país.
    """
    if operator:
        field, countries = ensure_country_filter(operator)
        return (
            table("products_v2")
            .select("*")
            .in_(field, countries)
            .order("created_at", desc=True)
            .execute()
        )

    return (
        table("products_v2")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )


# ============================================================
# OBTENER PRODUCTO
# ============================================================

def get_product_v2(product_id: str):
    result = (
        table("products_v2")
        .select("*")
        .eq("id", product_id)
        .single()
        .execute()
    )
    return result


# ============================================================
# CREAR PRODUCTO
# ============================================================

def create_product_v2(data: dict):
    data["created_at"] = datetime.utcnow().isoformat()
    res = table("products_v2").insert(data).execute()
    return res[0] if res else None


# ============================================================
# ACTUALIZAR PRODUCTO
# ============================================================

def update_product_v2(product_id: str, data: dict):
    data["updated_at"] = datetime.utcnow().isoformat()
    res = (
        table("products_v2")
        .update(data)
        .eq("id", product_id)
        .execute()
    )
    return res[0] if res else None


# ============================================================
# ELIMINAR PRODUCTO
# ============================================================

def delete_product_v2(product_id: str):
    return (
        table("products_v2")
        .delete()
        .eq("id", product_id)
        .execute()
    )


# ============================================================
# PROVEEDORES (compatibilidad)
# ============================================================

def list_providers_v2():
    """
    Alias para compatibilidad con vistas antiguas.
    """
    return (
        table("providers_v2")
        .select("*")
        .order("name", asc=True)
        .execute()
    )


# ============================================================
# COMPATIBILIDAD LEGACY
# ============================================================

def list_products():
    """
    Alias legacy usado por vistas antiguas.
    """
    return list_products_v2()


def get_product(product_id: str):
    """
    Alias legacy (Engine Monitor y Product Details Pro lo usan).
    """
    return get_product_v2(product_id)
