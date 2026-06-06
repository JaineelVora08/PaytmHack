"""Privacy helpers for Network Intelligence mocks.

These helpers model the Person B privacy guarantees from the build spec:
rotating merchant hashes, k-anonymity, differential privacy style count noise,
and basic PII stripping before text leaves the merchant-local zone.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import random
import re


PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?91[\s-]?)?(?:0[\s-]?)?[6-9](?:[\s-]?\d){9}(?!\d)"
)


def _daily_salt() -> str:
    """Return a deterministic salt that rotates once per local calendar day."""

    today = _dt.date.today().isoformat()
    return f"khatavaani-network:{today}"


def hash_merchant(merchant_id: str) -> str:
    """Hash a merchant id with a rotating daily salt before aggregation."""

    payload = f"{_daily_salt()}:{merchant_id}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def add_noise(count: int) -> int:
    """Add approximately +/-15% gaussian noise to a count.

    The standard deviation is 15% of the count, which keeps most mock outputs
    close to the original number while avoiding exact cross-merchant counts.
    """

    if count <= 0:
        return 0

    noisy_count = random.gauss(mu=count, sigma=count * 0.15)
    return max(0, round(noisy_count))


def k_anonymous_signal(merchant_count: int) -> bool:
    """Allow a network signal only when at least 5 merchants contributed."""

    return merchant_count >= 5


def strip_pii_from_text(text: str) -> str:
    """Mask phone numbers in free text before external processing."""

    return PHONE_PATTERN.sub("[PHONE_MASKED]", text)
