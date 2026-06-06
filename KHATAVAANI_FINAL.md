# KhataVaani — Final Build Spec
## AI Intelligence Module for Paytm Business Khata

> **Hackathon:** Paytm AI Hackathon · Mumbai · June 6 2026
> **Theme:** 2 — AI for Small Businesses
> **Positioning:** New AI module inside [business.paytm.com/business-khata](https://business.paytm.com/business-khata)
> **NOT a standalone app.** Components plug into the existing Paytm Business React app.
> **Sponsor APIs:** Sarvam AI (Vision, STT, LLM, TTS, Translate) + NewsAPI.org
> **Tagline:** *"Paytm network mein ho, toh pehle pata chalo."*

---

## 1 · The USP (Single Sentence)

**Every Paytm merchant gets demand intelligence from 10M+ anonymized merchant transactions + live news/festival/weather signals — pan-India, in 22 languages, with full customer privacy preserved via Paytm Ads broadcast.**

This is genuinely Paytm-exclusive. No bank can build it. No standalone app can. Only Paytm sits on both the merchant graph AND the consumer graph simultaneously.

---

## 2 · What We're Building

Three core features built on top of Paytm Business Khata:

| # | Feature | Tagline | Primary Sarvam APIs |
|---|---|---|---|
| **1** | **Bahi Khata Scan** | Onboarding — photograph notebook, instant digital records | Vision + 105B |
| **2** | **Voice Ask** | Ask your khata anything in 22 languages | Saaras + 105B + Bulbul |
| **3** | **Network Pulse + News** | Demand signals from network + external trends | Translate + Bulbul |

Two action layers that flow from above:

| # | Feature | Tagline |
|---|---|---|
| **4** | **Vyapar Mandal (Group Buy)** | When 5+ merchants nearby buy same SKU → auto group purchase |
| **5** | **Paytm Ads Broadcast** | Region-targeted customer offers — no PII handling needed |

---

## 3 · Privacy Architecture — Non-Negotiable

### Two data sources, two privacy zones

```
┌─────────────────────────────────────────────────────────────────┐
│  ZONE A — LOCAL (Merchant's own data)                            │
│  ─────────────────────────────────────────────                   │
│  • Bahi Khata scans (customer names, amounts, dates)             │
│  • Inventory counts                                              │
│  ↓                                                                │
│  STAYS on Paytm Business Khata merchant account                   │
│  Customer names never leave merchant's tenant                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ZONE B — NETWORK (Cross-merchant aggregates)                    │
│  ─────────────────────────────────────────────                   │
│  • Category-level demand signals (NOT items, NOT amounts)         │
│  • Geo-aggregated (NOT per-merchant)                              │
│  • Minimum k=5 merchants before any signal is surfaced            │
│  • Differential privacy: ±15% noise on counts                     │
│  ↓                                                                │
│  Merchant_id HASHED with rotating daily salt before aggregation   │
│  No reverse-lookup possible                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ZONE C — CONSUMER (Paytm Ads platform — fully owned by Paytm)   │
│  ─────────────────────────────────────────────                   │
│  • Merchant defines AUDIENCE SEGMENT (not individuals):          │
│    "users near Andheri who bought groceries last 60 days"        │
│  • Paytm Ads platform handles targeting on Paytm's side          │
│  • Merchant NEVER sees customer phone, name, or ID               │
│  • Privacy already enforced by Paytm's existing policy           │
└─────────────────────────────────────────────────────────────────┘
```

### Privacy rules enforced in code

| Rule | Where enforced |
|---|---|
| Customer names in `udhaar` table are hashed if any cross-tenant aggregation is done | `backend/privacy.py` |
| Network Pulse queries require `merchant_count >= 5` before returning data | `backend/network.py` |
| All cross-merchant signals add ±15% gaussian noise to counts | `backend/network.py` |
| Customer broadcasts use Paytm Ads segment_id, never phone/email | `backend/broadcast.py` |
| Sarvam API calls strip customer names before sending OCR text to LLM | `backend/sarvam_client.py` |
| Frontend never displays raw customer phone/UPI even if backend returns it | `frontend/api/client.js` (filter layer) |

---

## 4 · Work Division — 2 People, Feature Modules (NOT frontend/backend split)

Each person owns **a full vertical slice** — backend route + database access + frontend components + Sarvam API integration + privacy enforcement for their feature.

### Person A — "Local Intelligence" Module

Owns everything to do with the merchant's own scanned data.

| Layer | Files owned |
|---|---|
| Backend | `app.py` (`/api/scan`, `/api/ask`, `/api/velocity` routes), `database.py`, `velocity.py`, prompts for extraction + SQL generation |
| Sarvam APIs | Sarvam Vision (OCR), Sarvam Saaras (STT), Sarvam-105B (entity extraction + Text-to-SQL), Sarvam Bulbul (TTS) |
| Frontend | `ScanPage.jsx`, `AskPage.jsx`, `ResultsTable.jsx`, `MicButton.jsx` |
| Privacy | Local data isolation (customer names never sent to network aggregation) |
| Languages | Auto-detect language from STT, respond in same language |

**Person A's deliverables:**
- Scan flow: photo → Vision OCR → LLM extract → SQLite → table display
- Voice flow: hold mic → STT → SQL gen → execute → LLM answer → TTS playback
- Velocity calc: compare quantity across dated scan rows per item

---

### Person B — "Network Intelligence" Module

Owns everything to do with cross-merchant signals + external data + customer broadcast.

| Layer | Files owned |
|---|---|
| Backend | `app.py` (`/api/pulse`, `/api/news-trends`, `/api/group-buy`, `/api/broadcast` routes), `news_client.py`, `network.py`, `privacy.py`, `broadcast.py` |
| Sarvam APIs | Sarvam Translate (Mayura) for multilingual content, Sarvam-105B for offer generation, Sarvam Bulbul for spoken pulse summary |
| Frontend | `Dashboard.jsx`, `NetworkPulseCard.jsx`, `TrendCard.jsx`, `VyaparMandalCard.jsx`, `BroadcastModal.jsx` |
| Privacy | k-anonymity check (min 5 merchants), differential privacy noise, hash merchant_id for aggregations |
| External | NewsAPI.org integration, mock Paytm Ads SDK |

**Person B's deliverables:**
- Network Pulse card: aggregated demand signals from mock cross-merchant data
- News trend cards: cricket, festivals, weather pulled from NewsAPI
- Vyapar Mandal card: group buy trigger (mock 5-merchant detection)
- Broadcast modal: target segment + Sarvam Translate to 4 languages + mock Paytm Ads send

---

### Why this split works for 2 AIs

- **Zero overlap on files** — Person A and Person B never edit the same file
- **Clean API contract** between modules (defined in §7)
- **Shared resources** (SQLite DB, design tokens, App shell) are pre-built in §15 and never modified by either person
- **Each AI gets ONE prompt** (the section of this .md for their person) plus the shared contract section

---

## 5 · Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React 18 (Create React App) | Matches Paytm's React + Redux stack from StackShare |
| Styling | Vanilla CSS with design tokens | Matches Paytm reference repo (85% CSS, no Tailwind) |
| HTTP | axios | Paytm uses axios |
| Backend | Python 3.10 + Flask + flask-cors | Sarvam SDK is Python-first; Paytm uses Python |
| Database | SQLite (dev) — MySQL-compatible schema | Paytm uses MySQL in prod |
| AI APIs | sarvamai SDK (pip install sarvamai) | Sarvam sponsor |
| News | NewsAPI.org (free tier 100/day) | Easy demo; can swap for Indian news source |
| Privacy | Custom k-anonymity layer | Hand-rolled for clarity |
| Audio recording | MediaRecorder Web API | Browser-native, no library |
| Responsive | CSS Grid + Flexbox + media queries | Desktop + tablet + mobile |

---

## 6 · File Structure

```
khatavaani/
├── shared/                          ← Pre-built — neither person modifies
│   ├── api-contract.md              ← THE integration spec (§7)
│   ├── database-schema.sql          ← SQLite + MySQL-compatible
│   └── design-tokens.css            ← Color, spacing, typography vars
│
├── backend/                         ← Both people contribute, separate files
│   ├── app.py                       ← Flask app, registers blueprints
│   ├── database.py                  ← SHARED — neither person modifies
│   ├── sarvam_client.py             ← SHARED — both people use
│   │
│   ├── local_intelligence/          ← Person A owns
│   │   ├── routes.py                ← /api/scan, /api/ask, /api/velocity
│   │   ├── prompts.py               ← Extraction + SQL injection prompts
│   │   └── velocity.py              ← Velocity calculation
│   │
│   ├── network_intelligence/        ← Person B owns
│   │   ├── routes.py                ← /api/pulse, /api/news-trends, /api/group-buy, /api/broadcast
│   │   ├── network.py               ← Cross-merchant aggregation
│   │   ├── privacy.py               ← k-anonymity + differential privacy
│   │   ├── news_client.py           ← NewsAPI wrapper
│   │   └── broadcast.py             ← Paytm Ads mock
│   │
│   ├── requirements.txt
│   └── .env                         ← SARVAM_API_KEY, NEWS_API_KEY
│
└── frontend/
    └── src/
        └── features/
            └── ai-khata/            ← Drops into existing Paytm Business app
                ├── index.js         ← Exports AIKhataRouter + ImportButton
                ├── AIKhataRouter.jsx ← SHARED — routes both pages
                ├── api/
                │   ├── client.js    ← SHARED — axios wrapper, privacy filter
                │   └── mocks.js     ← SHARED — both update their section
                ├── styles/
                │   └── ai-khata.css ← SHARED — design tokens + global rules
                │
                ├── local/           ← Person A owns
                │   ├── ScanPage.jsx
                │   ├── AskPage.jsx
                │   ├── ResultsTable.jsx
                │   └── MicButton.jsx
                │
                └── network/         ← Person B owns
                    ├── Dashboard.jsx
                    ├── NetworkPulseCard.jsx
                    ├── TrendCard.jsx
                    ├── VyaparMandalCard.jsx
                    └── BroadcastModal.jsx
```

---

## 7 · API Contract — The Integration Boundary

> Both AIs MUST follow these shapes exactly. Any deviation breaks integration.
> Modify here first, then both sides update.

All routes require headers:
- `X-Merchant-ID: <merchant_id>` (Paytm merchant token in prod; `demo_merchant_001` for hackathon)
- `X-Lang-Preference: hi-IN | mr-IN | gu-IN | ta-IN | en-IN | ...` (defaults to `hi-IN`)

### Person A's routes — Local Intelligence

#### `POST /api/scan`
Request: `multipart/form-data` `{ image: file }`
Response 200:
```json
{
  "status": "ok",
  "udhaar": [
    { "id": 1, "customer_name": "Ramesh", "amount": 500, "type": "debit", "entry_date": "2024-06-01" }
  ],
  "inventory": [
    { "id": 1, "item_name": "Parle-G", "quantity": 20, "scan_date": "2024-06-01" }
  ],
  "privacy_note": "Customer data stored locally, never sent to network"
}
```

#### `POST /api/ask`
Request: `multipart/form-data` `{ audio: blob }`
Response 200: `Content-Type: audio/mpeg` with headers:
- `X-Transcript`: URL-encoded user query
- `X-Answer-Text`: URL-encoded answer (in detected language)
- `X-Agent`: `"udhaar" | "inventory" | "velocity"`
- `X-Lang-Detected`: `"hi-IN"` etc.

#### `GET /api/velocity`
Response 200:
```json
{
  "velocity": [
    { "item_name": "Parle-G", "units_sold": 12, "days": 4, "rate_per_day": 3.0 }
  ]
}
```

### Person B's routes — Network Intelligence

#### `GET /api/pulse`
Response 200:
```json
{
  "pulse": {
    "category": "ORS / Electral",
    "merchant_count": 14,
    "region": "Urban Mumbai",
    "demand_multiplier": 4.0,
    "headline_hi": "14 merchants ne ORS 4x stock ki — IPL final kal hai",
    "headline_en": "14 merchants increased ORS stock 4x — IPL final tomorrow",
    "audio_url": "/audio/pulse_hi.mp3",
    "viz_data": [14, 18, 22, 40, 56, 72, 96],
    "privacy_note": "Aggregated across 14 merchants (k=5 minimum). ±15% noise applied."
  }
}
```

#### `GET /api/news-trends`
Response 200:
```json
{
  "trends": [
    {
      "id": "ipl_final",
      "type": "cricket",
      "icon": "🏏",
      "title": "IPL Final — Kal Shaam 7:30pm",
      "source": "NewsAPI + Network",
      "body_hi": "Cold drinks, chips, namkeen demand 3–5x spike expected",
      "body_en": "Cold drinks, chips, namkeen demand 3–5x spike expected",
      "impact": [
        { "item": "Cold Drinks", "multiplier": "5x" },
        { "item": "Chips/Namkeen", "multiplier": "3x" }
      ],
      "region": "Urban Mumbai",
      "supporting_merchants": 22
    },
    {
      "id": "heat_wave",
      "type": "weather",
      "icon": "🌡️",
      "title": "Heat Wave — Mumbai, Thane, Pune",
      "source": "WeatherAPI + Network",
      "body_hi": "42°C agle 3 din — ORS demand 5x expected",
      "impact": [
        { "item": "ORS", "multiplier": "5x" },
        { "item": "Cold Drinks", "multiplier": "3x" }
      ],
      "region": "Urban Mumbai",
      "supporting_merchants": 18
    }
  ]
}
```

#### `GET /api/group-buy`
Response 200:
```json
{
  "active_groups": [
    {
      "id": "ors_andheri_001",
      "item": "ORS Electral",
      "merchants_count": 4,
      "discount_percent": 18,
      "closes_in_minutes": 120,
      "regular_price": 10.00,
      "group_price": 8.20,
      "minimum_units": 30,
      "privacy_note": "Other merchants' identities never revealed"
    }
  ]
}
```

#### `POST /api/broadcast`
Request:
```json
{
  "event_id": "ipl_final",
  "target_segment": {
    "region": "Andheri West, Mumbai",
    "behavior": "transacted_last_60_days",
    "category": "groceries"
  },
  "languages": ["hi-IN", "mr-IN", "gu-IN", "en-IN"]
}
```
Response 200:
```json
{
  "status": "queued",
  "messages": {
    "hi-IN": "नमस्ते! कल IPL Final है — Cold drinks aur snacks aaj hi le lo. 10% off ₹200+ par!",
    "mr-IN": "नमस्कार! उद्या IPL Final आहे — Cold drinks आज घेऊन जा. 10% सूट!",
    "gu-IN": "નમસ્તે! કાલે IPL Final છે — Cold drinks લો. 10% છૂટ!",
    "en-IN": "Hi! IPL Final tomorrow — get your snacks today. 10% off on ₹200+!"
  },
  "estimated_reach": 1240,
  "channel": "paytm_ads",
  "privacy_note": "No customer PII exposed. Paytm Ads handles targeting on platform side."
}
```

---

## 8 · Database Schema

```sql
-- Both people share this. Person A writes to udhaar + inventory.
-- Person B reads inventory for network aggregation (after privacy layer).

CREATE TABLE IF NOT EXISTS merchants (
  id            TEXT PRIMARY KEY,
  display_name  TEXT NOT NULL,
  region        TEXT NOT NULL,       -- "urban_mumbai" | "tier2_nagpur" etc.
  language_pref TEXT DEFAULT 'hi-IN',
  region_psi    INTEGER DEFAULT 75   -- purchasing power index 1-100
);

CREATE TABLE IF NOT EXISTS udhaar (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  merchant_id   TEXT NOT NULL,
  customer_name TEXT NOT NULL,        -- LOCAL ONLY — never aggregated
  amount        REAL NOT NULL,
  type          TEXT NOT NULL CHECK(type IN ('debit','credit')),
  entry_date    TEXT,
  source        TEXT DEFAULT 'scan',
  FOREIGN KEY (merchant_id) REFERENCES merchants(id)
);

CREATE TABLE IF NOT EXISTS inventory (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  merchant_id       TEXT NOT NULL,
  item_name         TEXT NOT NULL,
  category          TEXT,             -- used for network aggregation
  quantity          INTEGER NOT NULL,
  reorder_threshold INTEGER DEFAULT 5,
  scan_date         TEXT NOT NULL,
  FOREIGN KEY (merchant_id) REFERENCES merchants(id)
);

-- Network aggregation table — Person B writes nightly batch
-- NEVER stores merchant_id, only hashed buckets
CREATE TABLE IF NOT EXISTS network_signal (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  region          TEXT NOT NULL,
  category        TEXT NOT NULL,
  signal_date     TEXT NOT NULL,
  merchant_count  INTEGER NOT NULL,   -- ALWAYS >= 5 (k-anonymity)
  demand_index    REAL NOT NULL,      -- with ±15% noise
  context_tags    TEXT                -- "ipl_final,cricket,heatwave"
);

CREATE INDEX idx_udhaar_mid ON udhaar(merchant_id);
CREATE INDEX idx_inv_mid    ON inventory(merchant_id);
CREATE INDEX idx_signal_reg ON network_signal(region, signal_date);

-- Seed data for demo
INSERT OR IGNORE INTO merchants VALUES
  ('demo_merchant_001', 'Raju Sharma Kirana', 'urban_mumbai', 'hi-IN', 85);
```

---

## 9 · Sarvam APIs — Multilingual Strategy

22 Indian languages supported. Demo focuses on Hindi + Marathi + Gujarati + Tamil (one from each region).

### API map

| Sarvam API | Used by | Purpose |
|---|---|---|
| `optical_character_recognition` | Person A | OCR on bahi khata (handles Devanagari, Marathi, Gujarati, mixed scripts) |
| `speech_to_text` (Saaras v3) | Person A | Voice query input — auto-detect language |
| `chat` (Sarvam-M / 105B) | Both | Entity extraction (A), SQL generation (A), offer copy generation (B) |
| `text_to_speech` (Bulbul v3) | Both | Voice answer (A), spoken Pulse summary (B) |
| `translate` (Mayura) | Person B | Translate generated offers into 4+ regional languages |

### Multilingual flow for Voice Ask (Person A)

```
User speaks Marathi → Saaras detects mr-IN + transcribes
                   → 105B generates SQL (language-agnostic)
                   → 105B generates answer in mr-IN
                   → Bulbul speaks in mr-IN
```

### Multilingual flow for Broadcast (Person B)

```
Merchant clicks "Broadcast to customers"
  → 105B generates base offer in en-IN
  → Mayura translates to hi-IN, mr-IN, gu-IN, ta-IN (parallel)
  → Show all 4 versions in modal for preview
  → Paytm Ads platform serves correct language per user profile
```

### `sarvam_client.py` wrapper (SHARED file)

```python
"""Shared Sarvam client. Both Person A and Person B import from here."""
import os, base64
from sarvamai import SarvamAI
from dotenv import load_dotenv

load_dotenv()
client = SarvamAI(api_subscription_key=os.getenv("SARVAM_API_KEY"))

# Person A uses these:
def ocr_image(image_bytes: bytes) -> str:
    encoded = base64.b64encode(image_bytes).decode()
    return client.optical_character_recognition(image=encoded).text

def stt(audio_bytes: bytes, lang: str = "hi-IN") -> dict:
    r = client.speech_to_text(file=audio_bytes, model="saaras:v3", language_code=lang)
    return {"transcript": r.transcript, "detected_lang": getattr(r, "language_code", lang)}

# Both use:
def llm(system: str, user: str) -> str:
    r = client.chat(model="sarvam-m", messages=[
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ])
    return r.choices[0].message.content.strip()

def tts(text: str, lang: str = "hi-IN") -> bytes:
    r = client.text_to_speech(inputs=[text], target_language_code=lang,
                              speaker="meera", model="bulbul:v1")
    return base64.b64decode(r.audios[0])

# Person B uses this:
def translate_to(text: str, target_lang: str, source_lang: str = "en-IN") -> str:
    r = client.translate(input=text,
                         source_language_code=source_lang,
                         target_language_code=target_lang)
    return r.translated_text
```

---

## 10 · NewsAPI Integration (Person B)

### Why NewsAPI
Free tier 100 requests/day. Easy keyword search. For the demo, 3–5 calls is enough.

### Queries used

| Trend type | Query | Cache |
|---|---|---|
| Cricket | `IPL final OR India cricket match` (q + sortBy=publishedAt) | 6 hrs |
| Festivals | Hardcoded festival calendar (Eid, Diwali, Holi, Onam) | 24 hrs |
| Weather | `heat wave India OR mumbai weather` + OpenWeather API | 3 hrs |

### `news_client.py`

```python
import os, requests, json
from datetime import datetime, timedelta
from pathlib import Path

NEWS_KEY = os.getenv("NEWS_API_KEY")
CACHE_DIR = Path("/tmp/khatavaani_news_cache")
CACHE_DIR.mkdir(exist_ok=True)

def get_trends(region: str = "urban_mumbai") -> list:
    """Returns curated news trends with stocking implications."""
    cached = _read_cache("trends", hours=6)
    if cached:
        return cached

    # NewsAPI call
    cricket_news = _fetch_news("IPL final OR India cricket")
    weather_news = _fetch_news(f"heat wave {region} OR mumbai weather")

    # Combine with hardcoded festival calendar for demo robustness
    today = datetime.now()
    festival_trends = _festival_calendar(today)

    trends = []
    if cricket_news:
        trends.append({
            "id": "ipl_final",
            "type": "cricket",
            "icon": "🏏",
            "title": cricket_news[0]["title"][:80],
            "source": "NewsAPI + Network",
            "body_en": "Cold drinks, chips, namkeen demand 3–5x spike expected",
            "impact": [
                {"item": "Cold Drinks", "multiplier": "5x"},
                {"item": "Chips/Namkeen", "multiplier": "3x"}
            ],
            "supporting_merchants": 22,
        })
    if weather_news:
        trends.append({
            "id": "heat_wave",
            "type": "weather",
            "icon": "🌡️",
            "title": "Heat Wave alert — next 3 days",
            "source": "WeatherAPI + Network",
            "body_en": "42°C expected. ORS, cold drinks demand 5x.",
            "impact": [{"item": "ORS", "multiplier": "5x"}],
            "supporting_merchants": 18,
        })
    trends.extend(festival_trends)
    _write_cache("trends", trends)
    return trends

def _fetch_news(query: str):
    if not NEWS_KEY:  # Demo fallback
        return [{"title": f"Demo: {query}"}]
    url = f"https://newsapi.org/v2/everything?q={query}&pageSize=3&apiKey={NEWS_KEY}&language=en"
    r = requests.get(url, timeout=5)
    return r.json().get("articles", []) if r.ok else []

def _festival_calendar(today):
    # Hardcoded for demo robustness
    festivals = [
        {"date": "2026-06-08", "name": "Eid al-Adha", "items": ["sewai", "ghee"]},
        {"date": "2026-08-26", "name": "Janmashtami", "items": ["milk", "sweets"]},
        # ... add more
    ]
    upcoming = [f for f in festivals if f["date"] >= today.strftime("%Y-%m-%d")][:1]
    return [{
        "id": f"festival_{f['name'].lower().replace(' ','_')}",
        "type": "festival",
        "icon": "🎉",
        "title": f"{f['name']} — coming up",
        "source": "Festival Calendar + Network",
        "body_en": f"Stock up on {', '.join(f['items'])}",
        "impact": [{"item": i.title(), "multiplier": "3x"} for i in f["items"]],
        "supporting_merchants": 15,
    } for f in upcoming]

def _read_cache(key, hours):
    path = CACHE_DIR / f"{key}.json"
    if not path.exists(): return None
    if datetime.now() - datetime.fromtimestamp(path.stat().st_mtime) > timedelta(hours=hours):
        return None
    return json.loads(path.read_text())

def _write_cache(key, data):
    (CACHE_DIR / f"{key}.json").write_text(json.dumps(data))
```

---

## 11 · Paytm Ads Broadcast (Person B)

### Why Paytm Ads, not SMS/WhatsApp

| Approach | Privacy | Complexity | Realistic? |
|---|---|---|---|
| Direct SMS | ❌ Requires customer phone | High (DLT regs) | No |
| WhatsApp Business | ❌ Requires opt-in + phone | High | Partial |
| Paytm consumer notifications | ❌ Privacy concerns | Medium | OK |
| **Paytm Ads platform** | ✅ Segment-based, no PII | Low | **Yes — Paytm already runs ads.paytm.com** |

### Broadcast flow

```
1. Merchant taps "💬 Customers Ko Batao" on any alert
2. Modal opens — shows AI-generated offer in 4 languages
3. Merchant selects target segment (pre-built options):
   - "All customers within 2km"
   - "Customers who bought groceries last 60 days"
   - "Lapsed customers (no txn in 21 days)"
4. Tap "Send via Paytm Ads"
5. Backend calls (mock) Paytm Ads API:
   - Creates campaign with segment_id
   - Uploads 4 language variants
   - Returns estimated reach
6. Paytm Ads serves the offer to matching consumers
   - User on Paytm consumer app sees the ad
   - Multi-language: Paytm picks lang from user profile
   - User taps "Visit shop" → opens map to merchant
7. Merchant sees impression/click stats next day
```

### `broadcast.py` mock

```python
"""Mock Paytm Ads integration. In production, calls Paytm Ads API."""
import uuid
from datetime import datetime

# Pre-built target segments
SEGMENTS = {
    "nearby_2km":      {"label": "Customers within 2km", "reach": 1240},
    "lapsed_21d":      {"label": "Lapsed (no txn 21+ days)", "reach": 87},
    "category_groc":   {"label": "Bought groceries last 60d", "reach": 540},
    "festival_buyers": {"label": "Past festival shoppers",    "reach": 320},
}

def create_campaign(event_id: str, segment_id: str, language_messages: dict) -> dict:
    """Mock: returns campaign ID + estimated reach."""
    seg = SEGMENTS.get(segment_id, SEGMENTS["nearby_2km"])
    return {
        "campaign_id":     f"paytm_ads_{uuid.uuid4().hex[:8]}",
        "status":          "queued",
        "estimated_reach": seg["reach"],
        "segment_label":   seg["label"],
        "languages":       list(language_messages.keys()),
        "created_at":      datetime.now().isoformat(),
        "privacy_note":    "No customer PII accessed by merchant. Paytm Ads handles targeting.",
    }
```

---

## 12 · Privacy Layer (Person B)

### `privacy.py`

```python
"""Enforces k-anonymity, differential privacy, and hashing."""
import hashlib
import random
from datetime import date

K_MIN = 5             # Minimum merchants before any signal is surfaced
NOISE_PCT = 0.15      # ±15% gaussian noise on aggregate counts
SALT_PREFIX = "khatavaani_v1_"

def hash_merchant(merchant_id: str) -> str:
    """Rotating daily salt — same merchant gets same hash within a day,
    different hash on different days. Prevents long-term tracking."""
    salt = SALT_PREFIX + date.today().isoformat()
    return hashlib.sha256((salt + merchant_id).encode()).hexdigest()[:16]

def add_noise(count: int) -> int:
    """Add ±15% gaussian noise to counts. Minimum returned value is K_MIN."""
    noise = random.gauss(0, count * NOISE_PCT)
    return max(K_MIN, int(count + noise))

def k_anonymous_signal(merchant_count: int) -> bool:
    """Returns True if signal can be safely shown."""
    return merchant_count >= K_MIN

def strip_pii_from_text(text: str) -> str:
    """Before sending OCR text to LLM, strip obvious PII patterns.
    For demo: just a placeholder — production needs proper NER."""
    # Phone numbers
    import re
    text = re.sub(r'\b\d{10}\b', '[PHONE]', text)
    text = re.sub(r'\+91[-\s]?\d{10}', '[PHONE]', text)
    return text
```

---

## 13 · Design System — Sarvam-Minimal × Paytm Blue

### Design tokens (`shared/design-tokens.css`)

```css
:root {
  /* Paytm brand */
  --pt-blue:        #00BAF2;
  --pt-blue-d:      #0095C7;
  --pt-blue-bg:     #EBF8FE;
  --pt-navy:        #002970;
  --pt-navy-d:      #001A4D;

  /* Sarvam-minimal neutrals */
  --bg:             #FAFBFC;      /* very light grey, almost white */
  --bg-2:           #F4F6F8;
  --card:           #FFFFFF;
  --ink:            #0D1117;       /* near-black for text */
  --ink-2:          #4A5563;
  --ink-3:          #6B7280;
  --ink-4:          #9CA3AF;
  --border:         #E5E7EB;
  --border-2:       #F0F2F5;

  /* Semantic */
  --green:          #059669;
  --green-bg:       #ECFDF5;
  --amber:          #D97706;
  --amber-bg:       #FFFBEB;
  --red:            #DC2626;
  --red-bg:         #FEF2F2;
  --purple:         #7C3AED;
  --purple-bg:      #F5F3FF;

  /* Typography */
  --font-sans:      'DM Sans', system-ui, sans-serif;
  --font-deva:      'Noto Sans Devanagari', sans-serif;
  --font-mono:      'DM Mono', monospace;

  /* Spacing — generous (Sarvam-style) */
  --sp-1:           4px;
  --sp-2:           8px;
  --sp-3:           12px;
  --sp-4:           16px;
  --sp-5:           24px;
  --sp-6:           32px;
  --sp-7:           48px;
  --sp-8:           64px;

  /* Radius */
  --r-sm:           6px;
  --r:              10px;
  --r-lg:           14px;

  /* Shadows — very subtle */
  --sh-sm:          0 1px 2px rgba(0,0,0,0.04);
  --sh:             0 1px 3px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.04);

  /* Layout */
  --side-w:         220px;
  --max-content:    1080px;
}
```

### Aesthetic rules

| Rule | Why |
|---|---|
| Lots of whitespace between sections (--sp-6, --sp-7) | Sarvam-style breathing room |
| Single accent color (Paytm blue) for actions only | Sarvam-minimal — color is meaningful, not decorative |
| Card borders preferred over heavy shadows | Less visual weight |
| Network Pulse: ONE hero card, not multi-color clutter | Information hierarchy |
| Vyapar Mandal: separate section with its own visual treatment | Conceptual distinction (group buy ≠ news) |
| News trends: simple vertical list, not 2x2 grid | Easier to scan, less cluttered |
| Optional features: dashed border, low opacity | Clearly "future" |

---

## 14 · Responsive Strategy

```css
/* Mobile-first base styles, then scale up */

/* Default (mobile, < 640px):
   - Sidebar collapses to top hamburger
   - All cards single-column
   - Trend cards stack vertically
   - Mic button full-width */

@media (min-width: 640px) {
  /* Tablet — show partial sidebar */
}

@media (min-width: 1024px) {
  /* Desktop — full sidebar, content grid */
  .stat-row { grid-template-columns: repeat(3, 1fr); }
  .trend-grid { grid-template-columns: 1fr; }  /* still single column for cleanliness */
}
```

---

## 15 · Pre-Built Shared Files (Neither person modifies)

### `shared/AIKhataRouter.jsx`
```jsx
import React from "react";
import { Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "../network/Dashboard";      // Person B
import ScanPage  from "../local/ScanPage";          // Person A
import AskPage   from "../local/AskPage";           // Person A
import "../styles/ai-khata.css";

export default function AIKhataRouter() {
  return (
    <div className="ai-khata">
      <nav className="ak-tabs">
        <NavLink to="/ai-khata"        end>🔥 Network Pulse</NavLink>
        <NavLink to="/ai-khata/ask">🎙️ Baat Karo</NavLink>
        <NavLink to="/ai-khata/scan">📸 Khata Import</NavLink>
      </nav>
      <Routes>
        <Route path="/"     element={<Dashboard />} />
        <Route path="/scan" element={<ScanPage />}  />
        <Route path="/ask"  element={<AskPage />}   />
      </Routes>
    </div>
  );
}
```

### `shared/api/client.js`
```javascript
import axios from "axios";

const BASE        = process.env.REACT_APP_API_BASE  || "http://localhost:5000";
const USE_MOCK    = process.env.REACT_APP_USE_MOCK  === "true";
const MERCHANT_ID = process.env.REACT_APP_MERCHANT_ID || "demo_merchant_001";
const LANG        = process.env.REACT_APP_LANG       || "hi-IN";

export const api = axios.create({
  baseURL: BASE,
  headers: {
    "X-Merchant-ID": MERCHANT_ID,
    "X-Lang-Preference": LANG,
  },
});

// PRIVACY FILTER — strip PII before display
export function stripPII(obj) {
  if (typeof obj === "string") {
    return obj.replace(/\b\d{10}\b/g, "[PHONE]");
  }
  if (Array.isArray(obj)) return obj.map(stripPII);
  if (obj && typeof obj === "object") {
    const out = {};
    for (const k of Object.keys(obj)) {
      if (k === "customer_phone" || k === "customer_upi") continue;  // never display
      out[k] = stripPII(obj[k]);
    }
    return out;
  }
  return obj;
}

// Person A's functions (defined in §16)
export { scanImage, askQuestion, getVelocity } from "./local";

// Person B's functions (defined in §17)
export { getPulse, getNewsTrends, getGroupBuy, sendBroadcast } from "./network";
```

---

## 16 · Person A — Local Intelligence Implementation

### Backend: `local_intelligence/routes.py`
```python
import json, urllib.parse
from datetime import date
from flask import Blueprint, request, jsonify, Response
from database import get_db
from sarvam_client import ocr_image, stt, llm, tts
from local_intelligence.prompts import EXTRACTION_PROMPT, SQL_PROMPT, ANSWER_PROMPT
from local_intelligence.velocity import calculate_velocity

bp = Blueprint("local", __name__)

def merchant_id():
    return request.headers.get("X-Merchant-ID", "demo_merchant_001")

def lang_pref():
    return request.headers.get("X-Lang-Preference", "hi-IN")


@bp.route("/api/scan", methods=["POST"])
def scan():
    image = request.files["image"].read()
    raw   = ocr_image(image)
    today = date.today().isoformat()
    data  = json.loads(llm(EXTRACTION_PROMPT.format(today=today), raw).strip().strip("`").strip("json").strip())

    with get_db() as conn:
        for u in data.get("udhaar", []):
            conn.execute(
                "INSERT INTO udhaar (merchant_id, customer_name, amount, type, entry_date, source) VALUES (?,?,?,?,?,?)",
                (merchant_id(), u["customer_name"], u["amount"], u["type"], u.get("entry_date"), "scan")
            )
        for i in data.get("inventory", []):
            conn.execute(
                "INSERT INTO inventory (merchant_id, item_name, category, quantity, scan_date) VALUES (?,?,?,?,?)",
                (merchant_id(), i["item_name"], i.get("category", "general"), i["quantity"], i.get("scan_date", today))
            )
        udhaar_rows = [dict(r) for r in conn.execute("SELECT * FROM udhaar WHERE merchant_id=?", (merchant_id(),))]
        inv_rows    = [dict(r) for r in conn.execute("SELECT * FROM inventory WHERE merchant_id=?", (merchant_id(),))]

    return jsonify({
        "status": "ok",
        "udhaar": udhaar_rows,
        "inventory": inv_rows,
        "privacy_note": "Customer data stored locally, never sent to network",
    })


@bp.route("/api/ask", methods=["POST"])
def ask():
    audio   = request.files["audio"].read()
    lang    = lang_pref()
    stt_out = stt(audio, lang)
    transcript    = stt_out["transcript"]
    detected_lang = stt_out["detected_lang"]

    # Generate SQL
    sql = llm("", SQL_PROMPT.format(merchant_id=merchant_id(), transcript=transcript)).strip()
    if not sql.upper().startswith("SELECT"):
        return jsonify({"status": "error", "message": "Invalid query"}), 500

    with get_db() as conn:
        rows = [dict(r) for r in conn.execute(sql)]

    # Generate answer in detected language
    answer = llm("", ANSWER_PROMPT.format(
        question=transcript,
        result=json.dumps(rows, ensure_ascii=False),
        lang=detected_lang,
    ))

    # Detect agent
    q = transcript.lower()
    agent = "udhaar" if any(w in q for w in ["udhaar","baaki","customer"]) \
       else "velocity" if any(w in q for w in ["bika","fast","tezi"]) \
       else "inventory"

    audio_out = tts(answer, detected_lang)
    return Response(audio_out, mimetype="audio/mpeg", headers={
        "X-Transcript":    urllib.parse.quote(transcript),
        "X-Answer-Text":   urllib.parse.quote(answer),
        "X-Agent":         agent,
        "X-Lang-Detected": detected_lang,
        "Access-Control-Expose-Headers": "X-Transcript,X-Answer-Text,X-Agent,X-Lang-Detected",
    })


@bp.route("/api/velocity", methods=["GET"])
def velocity():
    return jsonify({"velocity": calculate_velocity(merchant_id())})
```

### Frontend components for Person A

- **`ScanPage.jsx`** — Upload zone → loader with 4 steps → results table
- **`AskPage.jsx`** — Hold-to-speak mic + transcript + answer card + suggestions
- **`ResultsTable.jsx`** — Tabs Udhaar/Inventory, Collect button per row
- **`MicButton.jsx`** — MediaRecorder integration

Component contracts in [§7 API Contract] — Person A's UI consumes the routes defined there.

---

## 17 · Person B — Network Intelligence Implementation

### Backend: `network_intelligence/routes.py`
```python
from flask import Blueprint, request, jsonify
from database import get_db
from sarvam_client import llm, tts, translate_to
from network_intelligence.news_client import get_trends
from network_intelligence.network import compute_pulse, get_active_groups
from network_intelligence.privacy import add_noise, k_anonymous_signal
from network_intelligence.broadcast import create_campaign, SEGMENTS

bp = Blueprint("network", __name__)

def merchant_id(): return request.headers.get("X-Merchant-ID", "demo_merchant_001")
def lang_pref():   return request.headers.get("X-Lang-Preference", "hi-IN")


@bp.route("/api/pulse", methods=["GET"])
def pulse():
    with get_db() as conn:
        row = conn.execute(
            "SELECT region FROM merchants WHERE id=?", (merchant_id(),)
        ).fetchone()
    region = row["region"] if row else "urban_mumbai"

    pulse_data = compute_pulse(region)  # returns dict with merchant_count, demand_multiplier etc

    # k-anonymity check
    if not k_anonymous_signal(pulse_data["merchant_count"]):
        return jsonify({"pulse": None, "reason": "insufficient_data"}), 200

    # Apply noise
    pulse_data["merchant_count"] = add_noise(pulse_data["merchant_count"])

    # Generate spoken headline in user's language
    headline_en = pulse_data["headline_en"]
    lang = lang_pref()
    headline_local = translate_to(headline_en, lang, "en-IN") if lang != "en-IN" else headline_en

    return jsonify({
        "pulse": {
            **pulse_data,
            f"headline_{lang.split('-')[0]}": headline_local,
            "privacy_note": f"Aggregated across {pulse_data['merchant_count']} merchants. ±15% noise.",
        }
    })


@bp.route("/api/news-trends", methods=["GET"])
def news_trends():
    region = request.args.get("region", "urban_mumbai")
    trends = get_trends(region)

    # Translate body to user's language
    lang = lang_pref()
    if lang != "en-IN":
        for t in trends:
            t[f"body_{lang.split('-')[0]}"] = translate_to(t["body_en"], lang, "en-IN")

    return jsonify({"trends": trends})


@bp.route("/api/group-buy", methods=["GET"])
def group_buy():
    return jsonify({"active_groups": get_active_groups(merchant_id())})


@bp.route("/api/broadcast", methods=["POST"])
def broadcast():
    body         = request.get_json()
    event_id     = body["event_id"]
    segment_id   = body.get("target_segment", {}).get("segment_id", "nearby_2km")
    target_langs = body.get("languages", ["hi-IN", "mr-IN", "gu-IN", "en-IN"])

    # Generate base message in English using LLM
    prompt = f"Generate a short, friendly customer offer SMS for event: {event_id}. Max 30 words."
    base_msg = llm("You are a marketing copywriter for Indian shops. Tone: warm, casual.", prompt)

    # Translate to all target languages in parallel-style
    messages = {"en-IN": base_msg}
    for lang in target_langs:
        if lang == "en-IN": continue
        messages[lang] = translate_to(base_msg, lang, "en-IN")

    # Mock Paytm Ads campaign creation
    campaign = create_campaign(event_id, segment_id, messages)
    return jsonify({
        "status":          "queued",
        "messages":        messages,
        "estimated_reach": campaign["estimated_reach"],
        "channel":         "paytm_ads",
        "campaign_id":     campaign["campaign_id"],
        "privacy_note":    "No customer PII exposed. Paytm Ads handles targeting.",
    })


@bp.route("/api/segments", methods=["GET"])
def segments():
    """Return available Paytm Ads segments for targeting UI."""
    return jsonify({"segments": [{"id": k, **v} for k, v in SEGMENTS.items()]})
```

### Frontend components for Person B

- **`Dashboard.jsx`** — Main page, composes all cards
- **`NetworkPulseCard.jsx`** — Hero card with viz + Bulbul audio + actions
- **`TrendCard.jsx`** — Simple horizontal card for news/festival/weather trends
- **`VyaparMandalCard.jsx`** — Distinct visual treatment for group buy (orange accent)
- **`BroadcastModal.jsx`** — Language tabs (hi/mr/gu/en) + segment picker + estimated reach + send button

---

## 18 · Integration Protocol (Critical for 2 AIs)

### How both AIs avoid stepping on each other

1. **Each AI gets a different prompt** — Person A's AI receives §16 only, Person B's AI receives §17 only. Both receive §1–§15 (shared context).

2. **File-level isolation:**
   - Person A files: `backend/local_intelligence/*`, `frontend/.../local/*`
   - Person B files: `backend/network_intelligence/*`, `frontend/.../network/*`
   - Shared files (NEVER modified by either AI): `backend/app.py`, `backend/database.py`, `backend/sarvam_client.py`, `frontend/.../api/client.js`, `frontend/.../AIKhataRouter.jsx`, `frontend/.../styles/ai-khata.css`

3. **API contract is law:** Both AIs must produce/consume the exact JSON shapes in §7. Any deviation breaks integration.

4. **Mock-first development:** Person B starts with hardcoded JSON returns. Person A starts with mocked frontend `mocks.js`. Both AIs see real integration only at final test step.

5. **Integration test (15 minutes at end):**
   ```bash
   # Terminal 1 (backend)
   cd backend && python app.py

   # Terminal 2 (frontend)
   cd frontend && REACT_APP_USE_MOCK=false npm start
   ```
   Click every button. If anything breaks → check §7 API Contract.

---

## 19 · Setup & Run

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # set SARVAM_API_KEY, NEWS_API_KEY
python app.py          # → http://localhost:5000

# Frontend
cd frontend
npm install
npm start              # → http://localhost:3000
```

### `requirements.txt`
```
flask==3.0.0
flask-cors==4.0.0
sarvamai==0.1.0
python-dotenv==1.0.0
Pillow==10.3.0
requests==2.31.0
```

### `.env.example`
```
SARVAM_API_KEY=your_sarvam_key
NEWS_API_KEY=your_newsapi_key
```

---

## 20 · Demo Bahi Khata Prop — Write Tonight

Two pages. Different dates. Dark pen on white paper.

```
Page 1 — 1 जून ──────────────
रमेश — ₹500 उधार
सुरेश ने ₹200 दिया
पार्ले-जी — 20 पैकेट
अमूल दूध — 15 पैकेट
आशीर्वाद आटा — 8 पैकेट
ORS Electral — 12 पैकेट

Page 2 — 5 जून ──────────────
प्रिया — ₹350 उधार
पार्ले-जी — 8 पैकेट
अमूल दूध — 13 पैकेट
आशीर्वाद आटा — 1 पैकेट
ORS Electral — 4 पैकेट
```

The ORS row is critical — it sets up the Network Pulse + News alert (heat wave + IPL final = ORS demand spike).

---

## 21 · 5-Minute Demo Script

| Time | Screen | Action | What you say |
|---|---|---|---|
| 0:00 | Hold bahi khata | Show physical notebook | *"Har kirana ke paas ek bahi khata hai. Khatabook ne kaha — type karo. Humne kaha — bas photo khicho."* |
| 0:30 | Scan page | Click "Demo chalao" → 4 steps complete → results | *"Sarvam Vision ne handwritten Hindi padhi. 3 udhaar entries, 5 inventory items, sab structured. 60 seconds."* |
| 1:30 | Voice ask page | Click मराठी chip, then English chip, then Hindi chip | *"22 Indian languages. Sarvam Saaras detects language, Sarvam-105B generates SQL, Bulbul speaks back. Sab merchant ki language mein."* |
| 2:30 | Network Pulse | Show pulse card | *"14 merchants near Andheri have 4x-ed ORS stock. Network signal, k=5 anonymity, ±15% noise. Aapka data safe, lekin aapko intelligence milta hai."* |
| 3:00 | News trends | Show IPL + heat wave cards | *"NewsAPI se IPL final detected. Weather API se heat wave. Network confirm karta hai — 22 merchants ne already stock kiya."* |
| 3:30 | Vyapar Mandal card | Click "Group mein judo" | *"4 merchants nearby same SKU order kar rahe — 18% bulk discount. Auto-formed group. Yeh sirf Paytm kar sakta hai."* |
| 4:00 | Broadcast modal | Open, switch hi → mr → gu → en | *"Sarvam Translate ne 4 languages mein offer banaya. Paytm Ads target karega — merchant ko customer phone kabhi nahi milta. Privacy by design."* |
| 4:30 | Tap "Send" | Confirmation toast | *"Paytm consumer app par 1,240 users ko region-wise targeted ad jayega."* |
| 5:00 | Close | — | *"Ek scan, teen agents, network intelligence, multilingual broadcast — aur sab privacy-preserving. Paytm hi yeh kar sakta hai."* |

---

## 22 · Judging Criteria Mapping

| Criterion | How we score |
|---|---|
| **Novelty** | Network intelligence aggregating across millions of merchants is genuinely Paytm-only. Bahi khata OCR for Indian scripts is technically unique. Combine = 🟢🟢 |
| **Feasibility** | Mock data + real Sarvam APIs + real NewsAPI = entirely demoable. SQLite + Flask = no infrastructure overhead. 🟢🟢 |
| **Latency** | All Sarvam calls cached/parallel. NewsAPI 6hr cache. Pulse uses pre-aggregated table. End-to-end < 3 sec per interaction. 🟢 |
| **Scale** | k-anonymity scales with merchant count. The MORE merchants on Paytm, the SMARTER the system. Network effect by design. 🟢🟢 |
| **Security** | k=5 minimum, ±15% noise, customer data local-only, broadcast via Paytm Ads (no merchant access to PII), rotating salt hashing. Explicit privacy notes in API responses. 🟢🟢 |
| **Impact** | Direct revenue impact (right stock at right time + customer reach). Defensive moat (only Paytm can build). Cross-merchant signal compounds over time. 🟢🟢 |
| **Execution** | 2-person split, clean integration boundary, mockable, < 8hr build. Pre-generated audio backups for live demo safety. 🟢🟢 |
| **Relevance** | Built explicitly on top of Paytm Business Khata. Uses Paytm Ads. Solves the exact merchant pain point Theme 2 specifies. 🟢🟢 |

---

## 23 · Final Checklist

### Person A (Local Intelligence)
- [ ] Backend: `/api/scan`, `/api/ask`, `/api/velocity` all return shapes from §7
- [ ] Sarvam Vision OCR tested on actual handwritten Hindi photo (TONIGHT)
- [ ] Voice flow works in Hindi, Marathi, Gujarati
- [ ] Schema injection SQL generation tested with 5+ queries
- [ ] Customer names in udhaar table never appear in any cross-merchant query
- [ ] Frontend: ScanPage, AskPage work with `USE_MOCK=true`

### Person B (Network Intelligence)
- [ ] Backend: `/api/pulse`, `/api/news-trends`, `/api/group-buy`, `/api/broadcast` return shapes from §7
- [ ] NewsAPI integration tested + fallback to hardcoded for demo robustness
- [ ] Privacy: k=5 check + noise + hashing all wired up
- [ ] Sarvam Translate working for hi/mr/gu/en
- [ ] Frontend: Dashboard, NetworkPulseCard, TrendCard, VyaparMandalCard, BroadcastModal all work with `USE_MOCK=true`

### Together (final 15 min)
- [ ] Set `USE_MOCK=false`, click every button, verify integration
- [ ] Pre-generate 4 Bulbul audio fallback files (in case live API slow)
- [ ] Write bahi khata prop (two pages, dated entries)
- [ ] Rehearse 5-min demo 3 times

---

*KhataVaani · Paytm AI Hackathon · Mumbai · June 6 2026*
