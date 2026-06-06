"""SQLite access layer for KhataVaani.

This shared module stays tenant-safe by requiring every local-intelligence
query to include the current merchant_id.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("KHATAVAANI_DB_PATH", BASE_DIR / "data" / "khatavaani.sqlite3"))


def _dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict:
    return {column[0]: row[index] for index, column in enumerate(cursor.description)}


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = _dict_factory
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS merchants (
                id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL DEFAULT 'Demo Merchant',
                region TEXT NOT NULL DEFAULT 'urban_mumbai',
                language_pref TEXT NOT NULL DEFAULT 'hi-IN',
                region_psi INTEGER NOT NULL DEFAULT 75,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS udhaar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                merchant_id TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('debit', 'credit')),
                entry_date TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'scan',
                source_scan_id TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (merchant_id) REFERENCES merchants(id)
            );

            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                merchant_id TEXT NOT NULL,
                item_name TEXT NOT NULL,
                category TEXT,
                quantity REAL NOT NULL,
                reorder_threshold INTEGER NOT NULL DEFAULT 5,
                scan_date TEXT NOT NULL,
                unit TEXT NOT NULL DEFAULT 'units',
                source_scan_id TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (merchant_id) REFERENCES merchants(id)
            );

            CREATE TABLE IF NOT EXISTS network_signal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT NOT NULL,
                category TEXT NOT NULL,
                signal_date TEXT NOT NULL,
                merchant_count INTEGER NOT NULL CHECK(merchant_count >= 5),
                demand_index REAL NOT NULL,
                context_tags TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_udhaar_merchant_date
                ON udhaar(merchant_id, entry_date);
            CREATE INDEX IF NOT EXISTS idx_inventory_merchant_item_date
                ON inventory(merchant_id, item_name, scan_date);
            CREATE INDEX IF NOT EXISTS idx_signal_region_date
                ON network_signal(region, signal_date);
            """
        )
        _ensure_columns(conn)
        _migrate_inventory_scans(conn)


def ensure_merchant(merchant_id: str, region: str = "urban_mumbai") -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO merchants(id, display_name, region, language_pref, region_psi)
            VALUES (?, ?, ?, 'hi-IN', 75)
            ON CONFLICT(id) DO NOTHING
            """,
            (merchant_id, merchant_id.replace("_", " ").title(), region),
        )


def insert_udhaar_rows(merchant_id: str, rows: list[dict], source_scan_id: str) -> list[dict]:
    ensure_merchant(merchant_id)
    inserted: list[dict] = []

    with get_db() as conn:
        for row in rows:
            cursor = conn.execute(
                """
                INSERT INTO udhaar(merchant_id, customer_name, amount, type, entry_date, source_scan_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    merchant_id,
                    row["customer_name"],
                    float(row["amount"]),
                    row.get("type", "debit"),
                    row["entry_date"],
                    source_scan_id,
                ),
            )
            inserted.append(
                {
                    "id": cursor.lastrowid,
                    "customer_name": row["customer_name"],
                    "amount": float(row["amount"]),
                    "type": row.get("type", "debit"),
                    "entry_date": row["entry_date"],
                }
            )

    return inserted


def insert_inventory_rows(merchant_id: str, rows: list[dict], source_scan_id: str) -> list[dict]:
    ensure_merchant(merchant_id)
    inserted: list[dict] = []

    with get_db() as conn:
        for row in rows:
            # Check if there is an existing row for the same merchant, item_name (case-insensitive), and scan_date
            existing = conn.execute(
                """
                SELECT id FROM inventory
                WHERE merchant_id = ? AND lower(item_name) = lower(?) AND scan_date = ?
                """,
                (merchant_id, row["item_name"], row["scan_date"]),
            ).fetchone()

            if existing:
                conn.execute(
                    """
                    UPDATE inventory
                    SET quantity = ?, unit = ?, source_scan_id = ?, category = COALESCE(?, category)
                    WHERE id = ?
                    """,
                    (
                        float(row["quantity"]),
                        row.get("unit", "units"),
                        source_scan_id,
                        row.get("category"),
                        existing["id"],
                    ),
                )
                inserted.append(
                    {
                        "id": existing["id"],
                        "item_name": row["item_name"],
                        "quantity": float(row["quantity"]),
                        "scan_date": row["scan_date"],
                        "unit": row.get("unit", "units"),
                    }
                )
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO inventory(
                        merchant_id, item_name, category, quantity, scan_date, unit, source_scan_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        merchant_id,
                        row["item_name"],
                        row.get("category"),
                        float(row["quantity"]),
                        row["scan_date"],
                        row.get("unit", "units"),
                        source_scan_id,
                    ),
                )
                inserted.append(
                    {
                        "id": cursor.lastrowid,
                        "item_name": row["item_name"],
                        "quantity": float(row["quantity"]),
                        "scan_date": row["scan_date"],
                        "unit": row.get("unit", "units"),
                    }
                )

    return inserted



def query_rows(sql: str, params: dict) -> list[dict]:
    with get_db() as conn:
        return conn.execute(sql, params).fetchall()


def _migrate_inventory_scans(conn: sqlite3.Connection) -> None:
    legacy = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_scans'"
    ).fetchone()
    if not legacy:
        return

    conn.execute(
        """
        INSERT INTO inventory(merchant_id, item_name, quantity, scan_date, unit, source_scan_id, created_at)
        SELECT merchant_id, item_name, quantity, scan_date, unit, source_scan_id, created_at
        FROM inventory_scans legacy
        WHERE NOT EXISTS (
            SELECT 1
            FROM inventory current
            WHERE current.merchant_id = legacy.merchant_id
              AND current.item_name = legacy.item_name
              AND current.scan_date = legacy.scan_date
              AND current.quantity = legacy.quantity
        )
        """
    )


def _ensure_columns(conn: sqlite3.Connection) -> None:
    _add_column_if_missing(conn, "merchants", "language_pref", "TEXT NOT NULL DEFAULT 'hi-IN'")
    _add_column_if_missing(conn, "merchants", "region_psi", "INTEGER NOT NULL DEFAULT 75")
    _add_column_if_missing(conn, "udhaar", "source", "TEXT NOT NULL DEFAULT 'scan'")


def _add_column_if_missing(
    conn: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_definition: str,
) -> None:
    columns = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
