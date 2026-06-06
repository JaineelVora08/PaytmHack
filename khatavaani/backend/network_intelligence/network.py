"""Mock network aggregation for Person B's Network Intelligence module."""

from __future__ import annotations


def compute_pulse(region: str) -> dict:
    """Return a demo cross-merchant demand pulse for a region."""

    return {
        "category": "ORS / Electral",
        "merchant_count": 14,
        "region": region.replace("_", " ").title(),
        "demand_multiplier": 4.0,
        "headline_en": "14 merchants increased ORS / Electral stock 4x ahead of heat and cricket demand.",
        "headline_hi": "14 merchants ne heat aur cricket demand se pehle ORS / Electral stock 4x badhaya.",
    }


def get_active_groups(merchant_id: str) -> list[dict]:
    """Return active Vyapar Mandal group-buy opportunities for a merchant."""

    return [
        {
            "id": "ors_andheri_001",
            "item": "ORS Electral",
            "merchants_count": 4,
            "discount_percent": 18,
            "closes_in_minutes": 120,
            "regular_price": 10.00,
            "group_price": 8.20,
            "minimum_units": 30,
            "privacy_note": "Other merchants' identities never revealed",
        }
    ]
