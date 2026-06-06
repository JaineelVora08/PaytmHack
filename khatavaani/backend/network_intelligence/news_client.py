"""NewsAPI trend fetcher for Network Intelligence mocks."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


NEWS_KEY = os.getenv("NEWS_API_KEY")
CACHE_DIR = Path("/tmp/khatavaani_news_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

NEWS_ENDPOINT = "https://newsapi.org/v2/everything"
CRICKET_QUERY = "IPL final OR India cricket"
WEATHER_QUERY = "heat wave OR mumbai weather"


def get_trends(region: str = "urban_mumbai") -> list[dict]:
    """Return curated news and festival trends with stocking implications."""

    cricket_news = _fetch_cached_news("cricket", CRICKET_QUERY, ttl_hours=6)
    weather_news = _fetch_cached_news("weather", WEATHER_QUERY, ttl_hours=3)

    trends = []
    display_region = _display_region(region)

    if cricket_news:
        trends.append(
            {
                "id": "ipl_final",
                "type": "cricket",
                "title": cricket_news[0].get("title", "India cricket demand spike")[:80],
                "source": "NewsAPI + Network",
                "body_en": "Cold drinks, chips, and namkeen demand 3-5x spike expected.",
                "body_hi": "Cold drinks, chips aur namkeen ki demand 3-5x badh sakti hai.",
                "impact": [
                    {"item": "Cold Drinks", "multiplier": "5x"},
                    {"item": "Chips/Namkeen", "multiplier": "3x"},
                ],
                "region": display_region,
                "supporting_merchants": 22,
            }
        )

    if weather_news:
        trends.append(
            {
                "id": "heat_wave",
                "type": "weather",
                "title": weather_news[0].get("title", "Heat wave alert - Mumbai")[:80],
                "source": "NewsAPI + Network",
                "body_en": "Hot weather can lift ORS, Electral, and cold drinks demand up to 5x.",
                "body_hi": "Garmi mein ORS, Electral aur cold drinks ki demand 5x tak badh sakti hai.",
                "impact": [
                    {"item": "ORS / Electral", "multiplier": "5x"},
                    {"item": "Cold Drinks", "multiplier": "3x"},
                ],
                "region": display_region,
                "supporting_merchants": 18,
            }
        )

    if trends:
        trends.extend(_festival_calendar(region))
        return trends

    return _festival_calendar(region)


def _fetch_cached_news(cache_key: str, query: str, ttl_hours: int) -> list[dict]:
    cached = _read_cache(cache_key, ttl_hours)
    if cached is not None:
        return cached

    articles = _fetch_news(query)
    if articles:
        _write_cache(cache_key, articles)
    return articles


def _fetch_news(query: str) -> list[dict]:
    if not NEWS_KEY:
        return []

    params = urlencode(
        {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 3,
            "apiKey": NEWS_KEY,
        }
    )
    request = Request(f"{NEWS_ENDPOINT}?{params}", headers={"User-Agent": "khatavaani-demo/1.0"})

    try:
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return []

    if payload.get("status") != "ok":
        return []

    return payload.get("articles", []) or []


def _read_cache(cache_key: str, ttl_hours: int) -> list[dict] | None:
    cache_path = CACHE_DIR / f"{cache_key}.json"
    if not cache_path.exists():
        return None

    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        cached_at = datetime.fromisoformat(payload["cached_at"])
    except (OSError, KeyError, ValueError, json.JSONDecodeError):
        return None

    age_seconds = (datetime.now(timezone.utc) - cached_at).total_seconds()
    if age_seconds > ttl_hours * 60 * 60:
        return None

    articles = payload.get("articles")
    return articles if isinstance(articles, list) else None


def _write_cache(cache_key: str, articles: list[dict]) -> None:
    cache_path = CACHE_DIR / f"{cache_key}.json"
    payload = {
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "articles": articles,
    }
    cache_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _festival_calendar(region: str) -> list[dict]:
    display_region = _display_region(region)
    return [
        {
            "id": "eid",
            "type": "festival",
            "title": "Eid shopping window",
            "source": "Festival Calendar",
            "body_en": "Expected rise in sweets, dry fruits, seviyan, and gifting demand.",
            "body_hi": "Sweets, dry fruits, seviyan aur gifting ki demand badhne ki sambhavna hai.",
            "impact": [
                {"item": "Seviyan", "multiplier": "4x"},
                {"item": "Dry Fruits", "multiplier": "2x"},
            ],
            "region": display_region,
            "supporting_merchants": 16,
        },
        {
            "id": "janmashtami",
            "type": "festival",
            "title": "Janmashtami preparation",
            "source": "Festival Calendar",
            "body_en": "Milk, curd, butter, sweets, and pooja items can see higher demand.",
            "body_hi": "Milk, curd, butter, sweets aur pooja items ki demand badh sakti hai.",
            "impact": [
                {"item": "Milk/Curd", "multiplier": "3x"},
                {"item": "Sweets", "multiplier": "3x"},
            ],
            "region": display_region,
            "supporting_merchants": 12,
        },
    ]


def _display_region(region: str) -> str:
    return region.replace("_", " ").title()
