# backend_core/dashboard/views/engine_monitor.py

import streamlit as st
from datetime import datetime, timedelta

# ==============================
# IMPORTS DEL BACKEND
# ==============================
from backend_core.services.session_repository import (
    get_all_sessions,
    get_active_sessions,
    get_parked_sessions,
    get_finished_sessions,
    get_expired_sessions,
)
from backend_core.services.module_repository import (
    list_all_modules,
    get_module_for_session,
)
from backend_core.services.product_repository_v2 import get_product
from backend_core.services.adjudicator_engine import (
    get_seed_for_session,
    get_adjudication_record,
)
from backend_core.services.session_engine import (
    get_next_session_in_series,
)
from backend_core.services.audit_repository import list_audit_logs


# =========================================================
# RENDER PRINCIPAL DEL ENGINE MONITOR
# =========================================================
def render_engine_monitor():
    st.title("⚙️ Engine Monitor — Sistema Operativo Central")
    st.markdown(
        """
        Monitor integral del motor: sesiones, módulos, series, adjudicaciones y auditoría.
        ---
        """
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔵 Overview",
        "🟣 Sessions Inspector",
        "🟡 Deterministic Engine",
        "🟢 Modules",
        "🔴 Audit Logs",
    ])

    # =====================================================
    # TAB 1 — OVERVIEW
    # =====================================================
    with tab1:
        st.subheader("🔵 Estado general del sistema")

        active = get_active_sessions() or []
        parked = get_parked_sessions() or []
        finished = get_finished_sessions() or []
        expired = get_expired_sessions() or []

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Sesiones Activas", len(active))
        col2.metric("Sesiones Parked", len(parked))
        col3.metric("Finalizadas", len(finished))
        col4.metric("Expiradas", len(expired))

        st.markdown("### ⏳ Sesiones que expiran en 24h")
        soon = _get_sessions_expiring_soon(active + parked)
        if soon:
            for s in soon:
                _render_session_short(s)
        else:
            st.info("No hay sesiones próximas a expirar.")

    # =====================================================
    # TAB 2 — SESSIONS INSPECTOR
    # =====================================================
    with tab2:
        st.subheader("🟣 Sessions Engine Inspector")

        sessions = get_all_sessions() or []
        if not sessions:
            st.info("No hay sesiones registradas.")
        else:
            for s in sessions:
                with st.expander(f"Sesión {s['id']} — {s['status']}"):
                    _render_session_full(s)

    # =====================================================
    # TAB 3 — DETERMINISTIC ENGINE
    # =====================================================
    with tab3:
        st.subheader("🟡 Deterministic Engine Inspector")

        active = get_active_sessions() or []
        finished = get_finished_sessions() or []

        lista = active + finished

        if not lista:
            st.info("Sin sesiones activas o finalizadas.")
        else:
            for s in lista:
                with st.expander(f"Deterministic Engine — Sesión {s['id']}"):
                    _render_deterministic_block(s)

    # =====================================================
    # TAB 4 — MODULES
    # =====================================================
    with tab4:
        st.subheader("🟢 Modules Inspector")

        mods = list_all_modules() or []
        st.write(f"Total módulos: **{len(mods)}**")

        for m in mods:
            st.write(f"- {m['id']} — {m['module_code']} — Active: {m['is_active']}")

    # =====================================================
    # TAB 5 — AUDIT LOGS
    # =====================================================
    with tab5:
        st.subheader("🔴 Audit Logs")

        logs = list_audit_logs() or []
        if not logs:
            st.info("Sin logs registrados.")
        else:
            for log in logs:
                with st.expander(f"{log['event']} — {log['created_at']}"):
                    st.json(log)


# =============================================================
# HELPERS PARA VISUALIZAR SESIONES
# =============================================================

def _render_session_short(s):
    st.write(
        f"🕒 **{s['id']}** expira en { _time_to_expire(s) } · "
        f"Estado: **{s['status']}** · Pax: {s['pax_registered']}/{s['capacity']}"
    )


def _render_session_full(s):
    st.write(f"**Estado:** {s['status']}")
    st.write(f"**Aforo:** {s['pax_registered']} / {s['capacity']}")
    st.write(f"**Creada:** {s.get('created_at')}")
    st.write(f"**Expira en:** { _time_to_expire(s) }")

    # Producto
    prod = get_product(s["product_id"])
    if prod:
        st.write(f"**Producto:** {prod['name']} — {prod['price_final']}€")
        if prod.get("image_url"):
            st.image(prod["image_url"], width=120)

    # Módulo
    mod = get_module_for_session(s["id"])
    if mod:
        st.write(f"**Módulo:** {mod['module_code']} — {mod['id']}")

    # Next in series
    nxt = get_next_session_in_series(s["id"])
    if nxt:
        st.info(f"Next session in series: {nxt['id']}")
    else:
        st.write("No hay próxima sesión en la serie.")


def _render_deterministic_block(s):
    seed = get_seed_for_session(s["id"])
    st.write("**Seed Input:**")
    st.code(seed or "No seed")

    rec = get_adjudication_record(s["id"])
    if rec:
        st.write("**Hash Output:**")
        st.code(rec.get("hash_output"))

        st.write("**Winner:**")
        st.write(rec.get("winner_id"))
    else:
        st.warning("No adjudicación registrada aún.")


def _time_to_expire(s):
    exp = s.get("expires_at")
    if not exp:
        return "—"
    try:
        dt = datetime.fromisoformat(exp.replace("Z", ""))
        delta = dt - datetime.utcnow()
        return str(delta).split(".")[0]
    except:
        return "—"


def _get_sessions_expiring_soon(sessions):
    out = []
    for s in sessions:
        exp = s.get("expires_at")
        if not exp:
            continue
        try:
            dt = datetime.fromisoformat(exp.replace("Z", ""))
            if dt - datetime.utcnow() < timedelta(hours=24):
                out.append(s)
        except:
            pass
    return out
