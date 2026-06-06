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
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS udhaar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                merchant_id TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('debit', 'credit')),
                entry_date TEXT NOT NULL,
                source_scan_id TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (merchant_id) REFERENCES merchants(id)
            );

            CREATE TABLE IF NOT EXISTS inventory_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                merchant_id TEXT NOT NULL,
                item_name TEXT NOT NULL,
                quantity REAL NOT NULL,
                scan_date TEXT NOT NULL,
                unit TEXT NOT NULL DEFAULT 'units',
                source_scan_id TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (merchant_id) REFERENCES merchants(id)
            );

            CREATE INDEX IF NOT EXISTS idx_udhaar_merchant_date
                ON udhaar(merchant_id, entry_date);
            CREATE INDEX IF NOT EXISTS idx_inventory_merchant_item_date
                ON inventory_scans(merchant_id, item_name, scan_date);
            """
        )


def ensure_merchant(merchant_id: str, region: str = "urban_mumbai") -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO merchants(id, display_name, region)
            VALUES (?, ?, ?)
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
            cursor = conn.execute(
                """
                INSERT INTO inventory_scans(merchant_id, item_name, quantity, scan_date, unit, source_scan_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    merchant_id,
                    row["item_name"],
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
