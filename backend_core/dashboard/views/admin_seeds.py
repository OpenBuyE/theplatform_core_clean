# backend_core/dashboard/views/admin_seeds.py

import streamlit as st

from backend_core.services.product_seeder import seed_products_v2
from backend_core.services.operators_seeder import seed_operators
from backend_core.services.providers_seeder import seed_providers
from backend_core.services.wallets_seeder import seed_wallets
from backend_core.services.modules_seeder import seed_modules
from backend_core.services.session_batches_seeder import seed_session_batches
from backend_core.services.routing_rules_seeder import seed_routing_rules

from backend_core.services.audit_repository import log_event


def render_admin_seeds():
    st.title("🧪 Admin Seeds — PRO Edition")
    st.write("Herramientas internas para poblar tablas de desarrollo (idempotentes).")

    # ======================================
    # SEED ALL
    # ======================================
    st.subheader("🚀 Seed All (ecosistema completo)")
    if st.button("Seed ALL (Operators, Providers, Wallets, Modules, Products, Sessions, Routing)"):
        total = 0
        total += seed_operators()
        total += seed_providers()
        total += seed_wallets()
        total += seed_modules()
        total += seed_products_v2()
        total += seed_session_batches()
        total += seed_routing_rules()
        st.success(f"Seed ALL ejecutado. Total inserts (aprox): {total}")
        log_event("ADMIN_SEEDS", f"Seed ALL executed. Inserted ~{total} records.")

    st.markdown("---")

    # ======================================
    # SEEDERS INDIVIDUALES
    # ======================================

    st.subheader("🧑‍💼 Operators")
    if st.button("Seed Operators"):
        n = seed_operators()
        st.success(f"{n} operators inserted")

    st.subheader("🏪 Providers")
    if st.button("Seed Providers"):
        n = seed_providers()
        st.success(f"{n} providers inserted")

    st.subheader("💰 Wallets")
    if st.button("Seed Wallets"):
        n = seed_wallets()
        st.success(f"{n} wallets inserted")

    st.subheader("🧩 Modules")
    if st.button("Seed Modules"):
        n = seed_modules()
        st.success(f"{n} modules inserted")

    st.subheader("📦 Products V2")
    if st.button("Seed Products V2 (20 items)"):
        n = seed_products_v2()
        st.success(f"{n} products inserted")

    st.subheader("📚 Session Batches (5 parked sessions)")
    if st.button("Seed Session Batches"):
        n = seed_session_batches()
        st.success(f"{n} sessions inserted")

    st.subheader("🛠 Routing Rules")
    if st.button("Seed Routing Rules"):
        n = seed_routing_rules()
        st.success(f"{n} rules inserted")

    st.info("Todos los seeders son idempotentes: solo insertan si no existen.")
