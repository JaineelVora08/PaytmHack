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
            "id": "ors_electral_group_001",
            "merchant_id": merchant_id,
            "item": "ORS Electral",
            "status": "active",
            "merchants_count": 4,
            "minimum_units": 200,
            "current_units": 145,
            "mock_group_price": 16.5,
            "market_price": 22.0,
            "currency": "INR",
            "unit": "sachet",
            "privacy_note": "Merchant participation is aggregated; individual merchant identities are hidden.",
        }
    ]
