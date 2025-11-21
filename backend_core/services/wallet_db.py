"""
wallet_db.py
Base de datos interna del Wallet (SQLite)

Responsabilidades:
- Registrar depósitos confirmados
- Verificar si todos los depósitos de una sesión han sido autorizados
- Registrar liquidaciones
- Registrar devoluciones por fuerza mayor
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "wallet.db"


def get_conn():
    """Devuelve conexión SQLite (modo autocommit)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_wallet_db():
    """Crea tablas si no existen."""
    conn = get_conn()
    cur = conn.cursor()

    # ----------------------------------------
    # 1. Depósitos individuales de participantes
    # ----------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            participant_id TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'EUR',
            fintech_tx_id TEXT,
            status TEXT NOT NULL,          -- AUTHORIZED / FAILED
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Índice para búsqueda rápida
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_deposits_session
        ON deposits(session_id)
    """)

    # ----------------------------------------
    # 2. Estado agregado por sesión:
    #    - si todos los depósitos están OK
    #    - si se puede liquidar
    # ----------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS session_funding_status (
            session_id TEXT PRIMARY KEY,
            total_expected INTEGER NOT NULL,    -- capacidad
            total_received INTEGER NOT NULL,    -- nº de depósitos autorizados
            all_funded BOOLEAN NOT NULL         -- True/False
        )
    """)

    # ----------------------------------------
    # 3. Liquidaciones
    # ----------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settlements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            adjudicatario_id TEXT NOT NULL,
            fintech_batch_id TEXT,
            status TEXT NOT NULL,              -- SETTLED / FAILED
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ----------------------------------------
    # 4. Fuerza mayor (refund)
    # ----------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS force_majeure_refunds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            adjudicatario_id TEXT NOT NULL,
            product_amount REAL NOT NULL,
            currency TEXT DEFAULT 'EUR',
            fintech_refund_tx_id TEXT,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# Inicializa automáticamente al importar
init_wallet_db()
