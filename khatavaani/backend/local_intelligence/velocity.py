"""Velocity calculations for merchant-local inventory scans."""

from __future__ import annotations

from datetime import date

from database import query_rows


def calculate_velocity(merchant_id: str) -> list[dict]:
    rows = query_rows(
        """
        SELECT item_name, quantity, scan_date
        FROM inventory_scans
        WHERE merchant_id = :merchant_id
        ORDER BY lower(item_name), scan_date
        """,
        {"merchant_id": merchant_id},
    )

    by_item: dict[str, list[dict]] = {}
    for row in rows:
        by_item.setdefault(row["item_name"].strip(), []).append(row)

    velocity: list[dict] = []
    for item_name, item_rows in by_item.items():
        if len(item_rows) < 2:
            continue

        first = item_rows[0]
        last = item_rows[-1]
        first_date = date.fromisoformat(first["scan_date"])
        last_date = date.fromisoformat(last["scan_date"])
        days = max((last_date - first_date).days, 1)
        units_sold = max(0.0, float(first["quantity"]) - float(last["quantity"]))

        velocity.append(
            {
                "item_name": item_name,
                "units_sold": round(units_sold, 2),
                "days": days,
                "rate_per_day": round(units_sold / days, 2),
            }
        )

    return sorted(velocity, key=lambda row: row["rate_per_day"], reverse=True)
