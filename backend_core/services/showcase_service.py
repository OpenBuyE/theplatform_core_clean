# backend_core/services/showcase_service.py
from typing import List, Dict, Any, Optional

from backend_core.services.supabase_client import table


def list_active_showcases(
    *,
    category_id: Optional[str] = None,
    limit: int = 30,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Devuelve showcases activos (producto + sesión activa) de forma robusta,
    sin depender de una VIEW SQL.

    - ca_sessions: id, product_id, status, capacity, created_at
    - products_v2: id, name, image_url, category_id, (precio puede variar)
    - ca_session_participants: session_id, quantity
    """

    # 1) Sesiones activas (paginadas)
    sessions = (
        table("ca_sessions")
        .select("id, product_id, status, capacity, created_at")
        .eq("status", "active")
        .range(offset, offset + limit - 1)
        .execute()
        .data
        or []
    )

    if not sessions:
        return []

    session_ids = [s["id"] for s in sessions if s.get("id")]
    product_ids = [s["product_id"] for s in sessions if s.get("product_id")]

    # 2) Productos (batch por IDs)
    #    Si hay category_id, filtramos aquí (más eficiente)
    prod_query = table("products_v2").select("id, name, image_url, category_id")
    if product_ids:
        prod_query = prod_query.in_("id", product_ids)
    if category_id:
        prod_query = prod_query.eq("category_id", category_id)

    products = prod_query.execute().data or []
    products_by_id = {p["id"]: p for p in products}

    # Si hay filtro por categoría, puede dejar fuera productos y por tanto sesiones:
    if category_id:
        sessions = [s for s in sessions if s.get("product_id") in products_by_id]
        session_ids = [s["id"] for s in sessions if s.get("id")]

    if not sessions:
        return []

    # 3) Participantes (batch por session_ids) y sumar quantity
    participants = []
    if session_ids:
        participants = (
            table("ca_session_participants")
            .select("session_id, quantity")
            .in_("session_id", session_ids)
            .execute()
            .data
            or []
        )

    filled_by_session: Dict[str, int] = {}
    for row in participants:
        sid = row.get("session_id")
        qty = int(row.get("quantity") or 0)
        if sid:
            filled_by_session[sid] = filled_by_session.get(sid, 0) + qty

    # 4) Construcción del payload "frontend-ready"
    out: List[Dict[str, Any]] = []
    for s in sessions:
        sid = s["id"]
        pid = s.get("product_id")
        p = products_by_id.get(pid, {}) if pid else {}

        capacity = int(s.get("capacity") or 0)
        filled = int(filled_by_session.get(sid, 0))

        out.append(
            {
                "product": {
                    "id": pid,
                    "name": p.get("name") or "Producto",
                    "category_id": p.get("category_id"),
                    "image_url": p.get("image_url"),
                    # precio: NO lo ponemos fijo porque en tu DB puede ser price_final u otro
                    # si quieres, lo añadimos cuando confirmes el campo real en products_v2
                },
                "session": {
                    "session_id": sid,
                    "status": s.get("status"),
                    "created_at": s.get("created_at"),
                    "capacity": capacity,
                    "filled_units": filled,
                },
                "progress": {
                    "label": f"{filled}/{capacity}" if capacity > 0 else "0/0",
                    "percent": round((filled / capacity) * 100, 2) if capacity > 0 else 0,
                },
            }
        )

    return out
