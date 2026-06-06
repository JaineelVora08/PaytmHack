"""Seed KhataVaani demo data for local preview and API smoke tests."""

from __future__ import annotations

from database import ensure_merchant, get_db, init_db


MERCHANT_ID = "demo_merchant_001"


UDHAAR_ROWS = [
    ("Ramesh Kirana", 500, "debit", "2026-06-01", "demo_seed"),
    ("Sita Stores", 200, "credit", "2026-06-02", "demo_seed"),
    ("Amit Snacks", 750, "debit", "2026-06-03", "demo_seed"),
    ("Neha Dairy", 320, "debit", "2026-06-04", "demo_seed"),
]

INVENTORY_ROWS = [
    ("Parle-G", "biscuits", 48, "2026-06-01", "packets", "seed_old"),
    ("Parle-G", "biscuits", 18, "2026-06-06", "packets", "seed_new"),
    ("Amul Milk", "dairy", 40, "2026-06-01", "litres", "seed_old"),
    ("Amul Milk", "dairy", 14, "2026-06-06", "litres", "seed_new"),
    ("ORS Electral", "health", 16, "2026-06-01", "sachets", "seed_old"),
    ("ORS Electral", "health", 4, "2026-06-06", "sachets", "seed_new"),
    ("Cold Drinks", "beverages", 72, "2026-06-01", "bottles", "seed_old"),
    ("Cold Drinks", "beverages", 20, "2026-06-06", "bottles", "seed_new"),
]

NETWORK_SIGNALS = [
    ("urban_mumbai", "ORS / Electral", "2026-06-06", 14, 4.0, "heatwave,cricket"),
    ("urban_mumbai", "Cold Drinks", "2026-06-06", 22, 5.0, "ipl_final,heatwave"),
    ("urban_mumbai", "Chips/Namkeen", "2026-06-06", 18, 3.0, "ipl_final"),
]


def seed_demo_data() -> None:
    init_db()
    ensure_merchant(MERCHANT_ID, "urban_mumbai")

    with get_db() as conn:
        conn.execute("DELETE FROM udhaar WHERE merchant_id=?", (MERCHANT_ID,))
        conn.execute("DELETE FROM inventory WHERE merchant_id=?", (MERCHANT_ID,))
        conn.execute("DELETE FROM network_signal WHERE region='urban_mumbai'")

        conn.executemany(
            """
            INSERT INTO udhaar(merchant_id, customer_name, amount, type, entry_date, source_scan_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [(MERCHANT_ID, *row) for row in UDHAAR_ROWS],
        )
        conn.executemany(
            """
            INSERT INTO inventory(
                merchant_id, item_name, category, quantity, scan_date, unit, source_scan_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [(MERCHANT_ID, *row) for row in INVENTORY_ROWS],
        )
        conn.executemany(
            """
            INSERT INTO network_signal(region, category, signal_date, merchant_count, demand_index, context_tags)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            NETWORK_SIGNALS,
        )


def print_summary() -> None:
    with get_db() as conn:
        for table in ("merchants", "udhaar", "inventory", "network_signal"):
            row = conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
            print(f"{table}: {row['count']}")

        print("\nLatest inventory:")
        for row in conn.execute(
            """
            SELECT item_name, quantity, unit, scan_date
            FROM inventory
            WHERE merchant_id=?
            ORDER BY scan_date DESC, item_name
            LIMIT 8
            """,
            (MERCHANT_ID,),
        ).fetchall():
            print(row)


if __name__ == "__main__":
    seed_demo_data()
    print_summary()
