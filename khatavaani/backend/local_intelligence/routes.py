"""Flask routes for Person A's Local Intelligence module."""

from __future__ import annotations

import json
import re
import unicodedata
import uuid
from datetime import date
from difflib import SequenceMatcher
from urllib.parse import quote

from flask import Blueprint, Response, jsonify, request

from database import insert_inventory_rows, insert_udhaar_rows, query_rows
from local_intelligence.prompts import ANSWER_SYSTEM, EXTRACT_RECORDS_SYSTEM, SQL_SYSTEM
from local_intelligence.velocity import calculate_velocity
from sarvam_client import llm, redact_likely_customer_names, stt, strip_customer_pii, tts, vision_ocr


local = Blueprint("local_intelligence", __name__)

DATE_PATTERNS = [
    re.compile(r"\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b"),
    re.compile(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](20\d{2})\b"),
]
AMOUNT_PATTERN = re.compile(r"(?:₹|rs\.?|inr)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)", re.I)
QTY_PATTERN = re.compile(r"\b(?:qty|quantity|stock|pcs?|pieces?|packets?|units?)\s*[:=-]?\s*(\d+(?:\.\d+)?)\b", re.I)
KNOWN_WORDS = {
    "debit",
    "credit",
    "paid",
    "payment",
    "jama",
    "udhaar",
    "qty",
    "quantity",
    "stock",
    "pcs",
    "piece",
    "pieces",
    "packet",
    "packets",
    "rs",
    "inr",
    "उधार",
    "जमा",
    "माल",
    "બાકી",
    "ઉધાર",
    "જમા",
    "માલ",
    "கடன்",
    "ஜமா",
    "சரக்கு",
    "స్టాక్",
    "అప్పు",
    "జమ",
    "ಉಧಾರ",
    "ಜಮಾ",
    "ಮಾಲು",
    "বাকি",
    "জমা",
}
UDHAAR_BALANCE_WORDS = {
    "baaki",
    "baki",
    "balance",
    "due",
    "left",
    "owe",
    "owes",
    "udhar",
    "udhaar",
    "debt",
    "pending",
    "kitna",
    "kitni",
    "कितना",
    "कितनी",
    "कितने",
    "बाकी",
    "उधार",
    "उधारी",
    "देना",
    "लेना",
    "બાકી",
    "ઉધાર",
    "જમા",
    "கடன்",
    "பாக்கி",
    "అప్పు",
    "బాకీ",
    "ಉಧಾರ",
    "ಬಾಕಿ",
    "বাকি",
}
INVENTORY_WORDS = {
    "stock",
    "inventory",
    "maal",
    "mal",
    "item",
    "quantity",
    "qty",
    "kitna",
    "kitni",
    "कितना",
    "कितनी",
    "कितने",
    "माल",
    "स्टॉक",
    "सामान",
    "कितना माल",
    "માલ",
    "સ્ટોક",
    "જથ્થો",
    "சரக்கு",
    "ஸ்டாக்",
    "எவ்வளவு",
    "స్టాక్",
    "సరుకు",
    "ఎంత",
    "ಮಾಲು",
    "ಸ್ಟಾಕ್",
    "ಎಷ್ಟು",
    "মাল",
    "স্টক",
    "কত",
}
QUESTION_STOP_WORDS = UDHAAR_BALANCE_WORDS | {
    "hai",
    "hain",
    "ka",
    "ke",
    "ki",
    "ko",
    "me",
    "mein",
    "mai",
    "mujhe",
    "bata",
    "batao",
    "kya",
    "how",
    "much",
    "is",
    "the",
    "for",
    "of",
    "tell",
    "show",
    "दिखाओ",
    "बताओ",
    "कितना",
    "कितनी",
    "कितने",
    "છે",
    "કેટલું",
    "बतાવો",
    "எவ்வளவு",
    "சொல்லு",
    "ఎంత",
    "చెప్పు",
    "ಎಷ್ಟು",
    "ಹೇಳು",
    "কত",
    "বলুন",
}


@local.route("/api/scan", methods=["POST"])
def scan():
    image = request.files.get("image")
    if image is None:
        return jsonify({"status": "error", "error": "image file is required"}), 400

    merchant_id = _merchant_id()
    source_scan_id = f"scan_{uuid.uuid4().hex[:12]}"

    # Use "auto" so Sarvam Vision auto-detects the script/language in the image.
    # Khata books can be in Hindi, Gujarati, Marathi, Tamil, Telugu, Kannada,
    # Bengali, or any mix — we should not pin this to the merchant's chat preference.
    ocr_text = vision_ocr(image, "auto")
    extracted = _extract_records(ocr_text)
    udhaar = insert_udhaar_rows(merchant_id, extracted["udhaar"], source_scan_id)
    inventory = insert_inventory_rows(merchant_id, extracted["inventory"], source_scan_id)

    return jsonify(
        {
            "status": "ok",
            "udhaar": udhaar,
            "inventory": inventory,
            "privacy_note": f"Saved {len(udhaar)} udhaar and {len(inventory)} inventory records to the local database.",
        }
    ), 200


@local.route("/api/ask", methods=["POST"])
def ask():
    audio = request.files.get("audio")
    transcript_override = request.form.get("transcript", "").strip()
    if audio is None and not transcript_override:
        return jsonify({"status": "error", "error": "audio blob or transcript is required"}), 400

    merchant_id = _merchant_id()
    preferred_lang = _lang_pref()

    speech = {"transcript": transcript_override, "language_code": preferred_lang}
    if audio is not None and not transcript_override:
        import sarvam_client as _sc
        if not _sc.SARVAM_API_KEY:
            # No API key — skip STT entirely, return clear guidance.
            answer = "Sarvam STT not configured. Type your question in the text box below instead."
            return _audio_response(b"", "", answer, "udhaar", preferred_lang)
        speech = stt(audio, "auto")

    transcript = speech.get("transcript") or ""
    detected_lang = speech.get("language_code") or preferred_lang

    if not transcript:
        # STT returned empty — key is set but audio transcription failed
        answer = "Audio samajh nahi aaya. Please speak clearly and try again, or type your question below."
        return _audio_response(b"", transcript, answer, "udhaar", detected_lang)

    agent, rows = _answer_rows(merchant_id, transcript)
    answer = _generate_answer(transcript, rows, agent, detected_lang)
    audio_bytes = tts(answer, detected_lang)
    return _audio_response(audio_bytes, transcript, answer, agent, detected_lang)


@local.route("/api/velocity", methods=["GET"])
def velocity():
    return jsonify({"velocity": calculate_velocity(_merchant_id())}), 200


@local.route("/api/records", methods=["GET"])
def records():
    merchant_id = _merchant_id()
    udhaar = query_rows(
        """
        SELECT customer_name, amount, type, entry_date
        FROM udhaar
        WHERE merchant_id = :merchant_id
        ORDER BY entry_date DESC, id DESC
        LIMIT 100
        """,
        {"merchant_id": merchant_id},
    )
    inventory = query_rows(
        """
        SELECT item_name, quantity, unit, scan_date
        FROM inventory
        WHERE merchant_id = :merchant_id
          AND scan_date = (
              SELECT MAX(latest.scan_date)
              FROM inventory latest
              WHERE latest.merchant_id = inventory.merchant_id
                AND lower(latest.item_name) = lower(inventory.item_name)
          )
        ORDER BY scan_date DESC, item_name
        LIMIT 100
        """,
        {"merchant_id": merchant_id},
    )
    return jsonify({"udhaar": udhaar, "inventory": inventory}), 200


def _extract_records(ocr_text: str) -> dict:
    sanitized_text = strip_customer_pii(ocr_text)
    model_response = llm(
        EXTRACT_RECORDS_SYSTEM,
        f"OCR text with contact PII masked:\n{sanitized_text}",
    )
    extracted = _parse_json_records(model_response)
    heuristic = _heuristic_extract(ocr_text)
    return {
        "udhaar": _merge_rows(
            heuristic["udhaar"],
            extracted["udhaar"],
            ("customer_name", "amount", "type", "entry_date"),
        ),
        "inventory": _merge_rows(
            extracted["inventory"],
            heuristic["inventory"],
            ("item_name", "quantity", "unit", "scan_date"),
        ),
    }


def _parse_json_records(text: str) -> dict:
    fallback = {"udhaar": [], "inventory": []}
    if not text:
        return fallback

    try:
        payload = json.loads(_json_object(text))
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback

    return {
        "udhaar": [_clean_udhaar(row) for row in payload.get("udhaar", []) if _clean_udhaar(row)],
        "inventory": [
            _clean_inventory(row) for row in payload.get("inventory", []) if _clean_inventory(row)
        ],
    }


def _heuristic_extract(text: str) -> dict:
    udhaar: list[dict] = []
    inventory: list[dict] = []
    current_date = date.today().isoformat()

    for raw_line in (text or "").splitlines():
        line = raw_line.strip(" -|\t")
        if not line:
            continue

        normalized_date = _line_date(line)
        if normalized_date:
            current_date = normalized_date

        lower = line.lower()
        qty_match = QTY_PATTERN.search(line)
        if qty_match:
            item_name = _clean_name(line[: qty_match.start()])
            item_name = _strip_date_amount(item_name)
            if item_name:
                inventory.append(
                    {
                        "item_name": item_name,
                        "quantity": float(qty_match.group(1)),
                        "unit": "units",
                        "scan_date": current_date,
                    }
                )
            continue

        if any(word in lower for word in ("debit", "credit", "paid", "jama", "udhaar", "₹", "rs")):
            amount_match = _last_amount(line)
            customer_name = _clean_name(line)
            customer_name = _strip_date_amount(customer_name)
            if amount_match and customer_name:
                row_type = "credit" if any(word in lower for word in ("credit", "paid", "jama")) else "debit"
                udhaar.append(
                    {
                        "customer_name": customer_name,
                        "amount": float(amount_match.replace(",", "")),
                        "type": row_type,
                        "entry_date": current_date,
                    }
                )

    return {"udhaar": udhaar, "inventory": inventory}


def _answer_rows(merchant_id: str, transcript: str) -> tuple[str, list[dict]]:
    fallback_agent, fallback_sql, fallback_params = _fallback_sql(transcript, merchant_id)
    if fallback_agent == "velocity":
        return "velocity", calculate_velocity(merchant_id)
    if fallback_agent == "inventory":
        return "inventory", _inventory_rows(merchant_id, transcript)
    if _is_udhaar_balance_question(transcript):
        return "udhaar", _udhaar_balance_rows(merchant_id, transcript)

    generated = llm(SQL_SYSTEM, _sql_user_prompt(merchant_id, transcript))
    agent, sql = _parse_sql(generated)
    if not _is_safe_sql(sql):
        agent, sql = fallback_agent, fallback_sql

    return agent, query_rows(sql, fallback_params)


def _generate_answer(transcript: str, rows: list[dict], agent: str, lang: str) -> str:
    if not rows:
        return {
            "hi-IN": "Is khate mein abhi is sawaal ka data nahi mila.",
            "en-IN": "I could not find matching local khata data yet.",
        }.get(lang, "Is khate mein abhi is sawaal ka data nahi mila.")

    if agent == "velocity":
        fastest = rows[0]
        return f"{fastest['item_name']} sabse fast chal raha hai: {fastest['rate_per_day']} units/day."
    if agent == "inventory":
        items = [
            f"{row['item_name']}: {row['quantity']} {row.get('unit', 'units')}"
            for row in rows[:8]
        ]
        return "Aapke latest stock mein hai: " + ", ".join(items) + "."
    if _is_balance_result(rows):
        return _format_udhaar_balance_answer(rows, lang)

    prompt = json.dumps(
        {
            "question": strip_customer_pii(transcript),
            "agent": agent,
            "answer_language": lang,
            "schema": _schema_context(),
            "rows": rows[:20],
        },
        ensure_ascii=False,
    )
    answer = llm(ANSWER_SYSTEM, prompt)
    if answer:
        return answer.strip()

    return f"Maine {len(rows)} matching local khata records dhoondhe."


def _udhaar_balance_rows(merchant_id: str, transcript: str) -> list[dict]:
    rows = query_rows(
        """
        SELECT
            customer_name,
            ROUND(SUM(CASE WHEN type = 'debit' THEN amount ELSE 0 END), 2) AS total_debit,
            ROUND(SUM(CASE WHEN type = 'credit' THEN amount ELSE 0 END), 2) AS total_credit,
            ROUND(SUM(CASE WHEN type = 'debit' THEN amount ELSE -amount END), 2) AS balance,
            MAX(entry_date) AS latest_entry_date
        FROM udhaar
        WHERE merchant_id = :merchant_id
        GROUP BY lower(customer_name)
        HAVING balance != 0
        ORDER BY latest_entry_date DESC, customer_name
        LIMIT 50
        """,
        {"merchant_id": merchant_id},
    )
    name_hint = _customer_name_hint(transcript)
    if not name_hint:
        return rows

    ranked = [(row, _name_match_score(name_hint, row["customer_name"])) for row in rows]
    matches = [row for row, score in ranked if score >= 0.62]
    if matches:
        return matches

    resolved_name = _resolve_local_name_with_llm(transcript, [row["customer_name"] for row in rows], "customer")
    if resolved_name:
        return [row for row in rows if row["customer_name"] == resolved_name]

    return rows


def _inventory_rows(merchant_id: str, transcript: str) -> list[dict]:
    rows = query_rows(
        """
        SELECT item_name, quantity, unit, scan_date
        FROM inventory
        WHERE merchant_id = :merchant_id
          AND scan_date = (
              SELECT MAX(latest.scan_date)
              FROM inventory latest
              WHERE latest.merchant_id = inventory.merchant_id
                AND lower(latest.item_name) = lower(inventory.item_name)
          )
        ORDER BY scan_date DESC, item_name
        LIMIT 50
        """,
        {"merchant_id": merchant_id},
    )
    item_hint = _entity_hint(transcript, QUESTION_STOP_WORDS | INVENTORY_WORDS)
    if not item_hint:
        return rows

    matches = [
        row
        for row in rows
        if _name_match_score(item_hint, row["item_name"]) >= 0.62
    ]
    if matches:
        return matches

    resolved_name = _resolve_local_name_with_llm(transcript, [row["item_name"] for row in rows], "inventory item")
    if resolved_name:
        return [row for row in rows if row["item_name"] == resolved_name]

    return rows


def _is_udhaar_balance_question(transcript: str) -> bool:
    lower = transcript.lower()
    return any(word in lower for word in UDHAAR_BALANCE_WORDS)


def _customer_name_hint(transcript: str) -> str:
    return _entity_hint(transcript, QUESTION_STOP_WORDS)


def _entity_hint(transcript: str, stop_words: set[str]) -> str:
    tokens = re.findall(r"[0-9A-Za-zÀ-ſऀ-ॿ઀-૿஀-௿ఀ-౿ಀ-೿ঀ-৿]+", transcript.lower())
    name_tokens = []
    for token in tokens:
        normalized = _normalize_text(token)
        if normalized in stop_words or token in stop_words or token.isdigit() or len(token) <= 1:
            continue
        name_tokens.append(token)
    return " ".join(name_tokens)


def _name_match_score(query: str, customer_name: str) -> float:
    query_norm = _loose_name(query)
    name_norm = _loose_name(customer_name)
    if not query_norm or not name_norm:
        return 0
    if query_norm in name_norm or name_norm in query_norm:
        return 1
    query_tokens = set(query_norm.split())
    name_tokens = set(name_norm.split())
    overlap = len(query_tokens & name_tokens) / max(len(query_tokens), 1)
    ratio = SequenceMatcher(None, query_norm, name_norm).ratio()
    return max(overlap, ratio)


def _loose_name(value: str) -> str:
    value = _normalize_text(value)
    value = re.sub(r"[^0-9a-zÀ-ſऀ-ॿ઀-૿஀-௿ఀ-౿ಀ-೿ঀ-৿]+", " ", value)
    value = re.sub(r"([a-z])\1+", r"\1", value)
    return " ".join(value.split())


def _normalize_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value or "").casefold()


def _resolve_local_name_with_llm(query: str, candidates: list[str], entity_type: str) -> str:
    if not candidates:
        return ""
    prompt = json.dumps(
        {
            "task": f"Match the user's {entity_type} mention to exactly one local database value.",
            "query": strip_customer_pii(query),
            "candidates": candidates[:50],
            "rules": [
                "The query and candidates may be in different Indian languages or scripts.",
                "Translate/transliterate mentally if needed.",
                "Return strict JSON only: {\"match\":\"candidate value\"}.",
                "If there is no clear match, return {\"match\":\"\"}.",
            ],
        },
        ensure_ascii=False,
    )
    response = llm(
        "You resolve multilingual Indian merchant query names to existing local database values.",
        prompt,
        temperature=0,
    )
    try:
        match = json.loads(_json_object(response)).get("match", "")
    except (TypeError, ValueError, json.JSONDecodeError):
        return ""
    return match if match in candidates else ""


def _is_balance_result(rows: list[dict]) -> bool:
    return (
        bool(rows)
        and {"customer_name", "balance"}.issubset(rows[0].keys())
        and rows[0]["balance"] is not None
    )


def _format_udhaar_balance_answer(rows: list[dict], lang: str) -> str:
    row = rows[0]
    balance = float(row["balance"])
    amount = abs(balance)
    if lang == "en-IN":
        if balance > 0:
            return f"{row['customer_name']} has ₹{amount:g} udhaar pending."
        return f"{row['customer_name']} has ₹{amount:g} extra credit."
    if balance > 0:
        return f"{row['customer_name']} ka ₹{amount:g} udhaar baaki hai."
    return f"{row['customer_name']} ka ₹{amount:g} advance/credit baaki hai."


def _sql_user_prompt(merchant_id: str, transcript: str) -> str:
    context = {
        "merchant_id_param": ":merchant_id",
        "question": strip_customer_pii(transcript),
        "schema": _schema_context(),
        "table_notes": {
            "udhaar_balance": "For baaki/udhaar balance, debit adds to debt and credit subtracts from debt.",
            "name_matching": "Customer names may be misspelled in speech; use the available customer list to choose the nearest local name.",
            "multilingual_lookup": "Stored customer and item names can be in Hindi, Gujarati, Tamil, Telugu, Kannada, Bengali, or English. Match the spoken query to the closest stored value before filtering.",
        },
        "available_customers": _known_customers(merchant_id),
        "available_items": _known_items(merchant_id),
    }
    return json.dumps(context, ensure_ascii=False)


def _schema_context() -> dict:
    return {
        "udhaar": {
            "columns": ["id", "merchant_id", "customer_name", "amount", "type", "entry_date"],
            "meaning": "Local udhaar/debt ledger. type='debit' means customer owes the shop; type='credit' means payment received.",
        },
        "inventory": {
            "columns": ["id", "merchant_id", "item_name", "category", "quantity", "unit", "scan_date"],
            "meaning": "Local inventory rows from scans.",
        },
    }


def _known_customers(merchant_id: str) -> list[str]:
    return [
        row["customer_name"]
        for row in query_rows(
            """
            SELECT DISTINCT customer_name
            FROM udhaar
            WHERE merchant_id = :merchant_id
            ORDER BY customer_name
            LIMIT 50
            """,
            {"merchant_id": merchant_id},
        )
    ]


def _known_items(merchant_id: str) -> list[str]:
    return [
        row["item_name"]
        for row in query_rows(
            """
            SELECT DISTINCT item_name
            FROM inventory
            WHERE merchant_id = :merchant_id
            ORDER BY item_name
            LIMIT 50
            """,
            {"merchant_id": merchant_id},
        )
    ]


def _fallback_sql(transcript: str, merchant_id: str) -> tuple[str, str, dict]:
    """Return (agent, sql, params) for the most likely query intent.

    Now extracts a customer name from the question when present, and uses a
    LIKE filter so "Ramesh kirana ka kitna udhar" actually returns Ramesh's rows.
    """
    lower = transcript.lower()

    # ── Velocity / speed queries ──────────────────────────────────────────────
    if any(word in lower for word in ("velocity", "fast", "speed", "rate", "jaldi", "tez", "बिक")):
        return "velocity", "", {"merchant_id": merchant_id}

    # ── Inventory / stock queries ─────────────────────────────────────────────
    if any(word in lower for word in ("stock", "inventory", "maal", "item", "quantity", "कितना माल")):
        sql = """
            SELECT item_name, quantity, unit, scan_date
            FROM inventory
            WHERE merchant_id = :merchant_id
              AND scan_date = (
                  SELECT MAX(latest.scan_date)
                  FROM inventory latest
                  WHERE latest.merchant_id = inventory.merchant_id
                    AND lower(latest.item_name) = lower(inventory.item_name)
              )
            ORDER BY scan_date DESC, item_name
            LIMIT 50
        """
        return "inventory", sql, {"merchant_id": merchant_id}

    # ── Udhaar / customer queries ─────────────────────────────────────────────
    # Try to extract a customer name from the question.
    # Strip known filler words and look for a proper noun sequence.
    customer_name = _extract_customer_name(transcript)

    if customer_name:
        sql = """
            SELECT customer_name, amount, type, entry_date
            FROM udhaar
            WHERE merchant_id = :merchant_id
              AND lower(customer_name) LIKE :name_like
            ORDER BY entry_date DESC, id DESC
            LIMIT 50
        """
        return "udhaar", sql, {
            "merchant_id": merchant_id,
            "name_like": f"%{customer_name.lower()}%",
        }

    # Generic udhaar — return all recent entries
    sql = """
        SELECT customer_name, amount, type, entry_date
        FROM udhaar
        WHERE merchant_id = :merchant_id
        ORDER BY entry_date DESC, id DESC
        LIMIT 50
    """
    return "udhaar", sql, {"merchant_id": merchant_id}


# Hindi/common filler words to strip when extracting a customer name
_FILLER_WORDS = {
    "ka", "ki", "ke", "ko", "se", "ne", "hai", "hain", "tha", "the",
    "kya", "kitna", "kitni", "kitne", "baaki", "bacha", "total", "udhar",
    "udhaar", "khata", "kirana", "shop", "dukan", "wala", "wali", "mera",
    "meri", "mera", "aapka", "aapki", "ramesh", "sita", "amit", "neha",
    "bata", "batao", "dikhao", "check", "dekho", "iska", "iski",
}

# Common shop-type suffixes — keep them as part of the name for LIKE matching
_SHOP_SUFFIXES = {"kirana", "store", "stores", "shop", "dukan", "dairy", "snacks", "mart"}


def _extract_customer_name(transcript: str) -> str:
    """Best-effort extraction of a customer/business name from a Hindi-English question.

    Strategy:
    1. Remove punctuation and split into tokens.
    2. Drop generic filler words.
    3. Treat consecutive capitalised or Hindi-looking tokens as the name.
    4. Also include shop-type suffixes (kirana, store, dairy, …) in the match
       since customer_name in DB is often "Ramesh Kirana" etc.
    """
    # Normalise
    tokens = re.sub(r"[^\w\s]", " ", transcript).split()

    # Build candidate tokens: anything that is NOT a pure filler word and
    # is either title-cased, all-caps, or contains Devanagari characters.
    name_tokens: list[str] = []
    for tok in tokens:
        lower = tok.lower()
        if lower in _FILLER_WORDS:
            continue
        # Include if it looks like a proper noun (capitalised) or a shop suffix
        if tok[0].isupper() or lower in _SHOP_SUFFIXES or re.search(r"[\u0900-\u097F]", tok):
            name_tokens.append(tok)

    if not name_tokens:
        return ""

    # Return first contiguous proper-noun run (max 3 words to avoid over-matching)
    return " ".join(name_tokens[:3])


def _parse_sql(response: str) -> tuple[str, str]:
    try:
        payload = json.loads(_json_object(response))
    except (TypeError, ValueError, json.JSONDecodeError):
        return "", ""
    return payload.get("agent", ""), payload.get("sql", "")


def _is_safe_sql(sql: str) -> bool:
    compact = " ".join((sql or "").strip().split()).lower()
    if not compact.startswith("select "):
        return False
    if ";" in compact or "--" in compact or "/*" in compact:
        return False
    if "merchant_id" not in compact or ":merchant_id" not in compact:
        return False
    forbidden = ("insert ", "update ", "delete ", "drop ", "alter ", "pragma ", "attach ")
    if any(word in compact for word in forbidden):
        return False
    table_matches = re.findall(r"\b(?:from|join)\s+([a-z_]+)", compact)
    return bool(table_matches) and all(table in {"udhaar", "inventory"} for table in table_matches)


def _audio_response(audio_bytes: bytes, transcript: str, answer: str, agent: str, lang: str) -> Response:
    response = Response(audio_bytes, mimetype="audio/mpeg")
    response.headers["X-Transcript"] = quote(transcript)
    response.headers["X-Answer-Text"] = quote(answer)
    response.headers["X-Agent"] = agent
    response.headers["X-Lang-Detected"] = lang
    return response


def _merchant_id() -> str:
    return request.headers.get("X-Merchant-ID", "demo_merchant_001")


def _lang_pref() -> str:
    return request.headers.get("X-Lang-Preference", "hi-IN")


def _line_date(line: str) -> str | None:
    for pattern in DATE_PATTERNS:
        match = pattern.search(line)
        if not match:
            continue
        groups = [int(group) for group in match.groups()]
        try:
            if groups[0] > 1900:
                return date(groups[0], groups[1], groups[2]).isoformat()
            return date(groups[2], groups[1], groups[0]).isoformat()
        except ValueError:
            return None
    return None


def _last_amount(line: str) -> str | None:
    matches = AMOUNT_PATTERN.findall(line)
    return matches[-1] if matches else None


def _strip_date_amount(value: str) -> str:
    for pattern in DATE_PATTERNS:
        value = pattern.sub("", value)
    value = re.sub(r"(?:₹|rs\.?|inr)?\s*\d+(?:,\d{3})*(?:\.\d+)?", "", value, flags=re.I)
    return _clean_name(value)


def _clean_name(value: str) -> str:
    tokens = re.sub(r"[^0-9A-Za-zÀ-ſऀ-ॿ\s.-]", " ", value).split()
    filtered = [token for token in tokens if token.lower() not in KNOWN_WORDS and not token.isdigit()]
    return " ".join(filtered).strip(" .-")


def _clean_udhaar(row: dict) -> dict | None:
    try:
        customer_name = str(row["customer_name"]).strip()
        if not customer_name:
            return None
        amount = float(row["amount"])
        row_type = row.get("type", "debit") if row.get("type") in {"debit", "credit"} else "debit"
        
        entry_date_val = row.get("entry_date")
        if entry_date_val:
            try:
                entry_date = date.fromisoformat(str(entry_date_val)[:10]).isoformat()
            except ValueError:
                entry_date = date.today().isoformat()
        else:
            entry_date = date.today().isoformat()
            
        return {
            "customer_name": customer_name,
            "amount": amount,
            "type": row_type,
            "entry_date": entry_date,
        }
    except (KeyError, TypeError, ValueError):
        return None


def _clean_inventory(row: dict) -> dict | None:
    try:
        item_name = str(row["item_name"]).strip()
        if not item_name:
            return None
        quantity = float(row["quantity"])
        unit = str(row.get("unit", "units")).strip() or "units"
        
        scan_date_val = row.get("scan_date")
        if scan_date_val:
            try:
                scan_date = date.fromisoformat(str(scan_date_val)[:10]).isoformat()
            except ValueError:
                scan_date = date.today().isoformat()
        else:
            scan_date = date.today().isoformat()
            
        return {
            "item_name": item_name,
            "quantity": quantity,
            "unit": unit,
            "scan_date": scan_date,
        }
    except (KeyError, TypeError, ValueError):
        return None


def _remove_masked_customers(rows: list[dict]) -> list[dict]:
    return [row for row in rows if "[CUSTOMER_NAME]" not in row.get("customer_name", "")]


def _merge_rows(primary: list[dict], secondary: list[dict], keys: tuple[str, ...]) -> list[dict]:
    merged: list[dict] = []
    seen: set[tuple] = set()
    for row in [*primary, *secondary]:
        row_key = tuple(row.get(key) for key in keys)
        if row_key in seen:
            continue
        seen.add(row_key)
        merged.append(row)
    return merged


def _json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found")
    return text[start : end + 1]
