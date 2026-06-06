"""Mock Paytm Ads integration for customer broadcasts.

The merchant selects audience segments only. Paytm Ads owns customer targeting,
so this mock never exposes customer identifiers to the merchant-facing module.
"""

from __future__ import annotations

import uuid


SEGMENTS = {
    "nearby_2km": 12400,
    "lapsed_21d": 6800,
    "category_groc": 18500,
    "festival_buyers": 9200,
}


def create_campaign(event_id, segment_id, language_messages):
    """Queue a mock Paytm Ads campaign for a segment-based broadcast."""

    if segment_id not in SEGMENTS:
        raise ValueError(f"Unknown segment_id: {segment_id}")

    return {
        "campaign_id": f"mock_ads_{uuid.uuid4().hex[:12]}",
        "event_id": event_id,
        "segment_id": segment_id,
        "status": "queued",
        "estimated_reach": SEGMENTS[segment_id],
        "language_messages": language_messages,
        "privacy_note": "No PII is exposed; Paytm Ads handles targeting by segment_id.",
    }
