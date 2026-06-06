"""Flask routes for Person A's Local Intelligence module."""

from __future__ import annotations

import json
import re
import uuid
from datetime import date
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
}


@local.route("/api/scan", methods=["POST"])
def scan():
    image = request.files.get("image")
    if image is None:
        return jsonify({"status": "error", "error": "image file is required"}), 400

    merchant_id = _merchant_id()
    lang = _lang_pref()
    source_scan_id = f"scan_{uuid.uuid4().hex[:12]}"

    ocr_text = vision_ocr(image, lang)
    extracted = _extract_records(ocr_text)
    udhaar = insert_udhaar_rows(merchant_id, extracted["udhaar"], source_scan_id)
    inventory = insert_inventory_rows(merchant_id, extracted["inventory"], source_scan_id)

    return jsonify(
        {
            "status": "ok",
            "udhaar": udhaar,
            "inventory": inventory,
            "privacy_note": "Customer data stored locally, never sent to network",
        }
    ), 200


@local.route("/api/ask", methods=["POST"])
def ask():
    audio = request.files.get("audio")
    transcript_override = request.form.get("transcript", "").strip()
    if audio is None and not transcript_override:
        return jsonify({"status": "error", "error": "audio blob is required"}), 400

    merchant_id = _merchant_id()
    preferred_lang = _lang_pref()

    speech = {"transcript": transcript_override, "language_code": preferred_lang}
    if audio is not None and not transcript_override:
        speech = stt(audio, "auto")

    transcript = speech.get("transcript") or ""
    detected_lang = speech.get("language_code") or preferred_lang

    if not transcript:
        answer = "Audio samajh nahi aaya. SARVAM_API_KEY add karke dobara try karein."
        return _audio_response(b"", transcript, answer, "udhaar", detected_lang)

    agent, rows = _answer_rows(merchant_id, transcript)
    answer = _generate_answer(transcript, rows, agent, detected_lang)
    audio_bytes = tts(answer, detected_lang)
    return _audio_response(audio_bytes, transcript, answer, agent, detected_lang)


@local.route("/api/velocity", methods=["GET"])
def velocity():
    return jsonify({"velocity": calculate_velocity(_merchant_id())}), 200


def _extract_records(ocr_text: str) -> dict:
    sanitized_text = redact_likely_customer_names(strip_customer_pii(ocr_text))
    model_response = llm(
        EXTRACT_RECORDS_SYSTEM,
        f"OCR text with contact PII masked:\n{sanitized_text}",
    )
    extracted = _parse_json_records(model_response)
    heuristic = _heuristic_extract(ocr_text)
    return {
        "udhaar": heuristic["udhaar"] or _remove_masked_customers(extracted["udhaar"]),
        "inventory": extracted["inventory"] or heuristic["inventory"],
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

    for raw_line in (text or "").splitlines():
        line = raw_line.strip(" -|\t")
        if not line:
            continue

        normalized_date = _line_date(line)
        if not normalized_date:
            continue

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
                        "scan_date": normalized_date,
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
                        "entry_date": normalized_date,
                    }
                )

    return {"udhaar": udhaar, "inventory": inventory}


def _answer_rows(merchant_id: str, transcript: str) -> tuple[str, list[dict]]:
    fallback_agent, fallback_sql = _fallback_sql(transcript)
    if fallback_agent == "velocity":
        return "velocity", calculate_velocity(merchant_id)

    generated = llm(SQL_SYSTEM, f"Merchant question: {strip_customer_pii(transcript)}")
    agent, sql = _parse_sql(generated)
    if not _is_safe_sql(sql):
        agent, sql = fallback_agent, fallback_sql

    return agent, query_rows(sql, {"merchant_id": merchant_id})


def _generate_answer(transcript: str, rows: list[dict], agent: str, lang: str) -> str:
    if not rows:
        return {
            "hi-IN": "Is khate mein abhi is sawaal ka data nahi mila.",
            "en-IN": "I could not find matching local khata data yet.",
        }.get(lang, "Is khate mein abhi is sawaal ka data nahi mila.")

    prompt = json.dumps(
        {
            "question": strip_customer_pii(transcript),
            "agent": agent,
            "answer_language": lang,
            "rows": rows[:20],
        },
        ensure_ascii=False,
    )
    answer = llm(ANSWER_SYSTEM, prompt)
    if answer:
        return answer.strip()

    if agent == "velocity":
        fastest = rows[0]
        return f"{fastest['item_name']} sabse fast chal raha hai: {fastest['rate_per_day']} units/day."
    return f"Maine {len(rows)} matching local khata records dhoondhe."


def _fallback_sql(transcript: str) -> tuple[str, str]:
    lower = transcript.lower()
    if any(word in lower for word in ("velocity", "fast", "speed", "rate", "jaldi", "tez", "बिक")):
        return "velocity", ""
    if any(word in lower for word in ("stock", "inventory", "maal", "item", "quantity", "कितना माल")):
        return (
            "inventory",
            """
            SELECT item_name, quantity, unit, scan_date
            FROM inventory_scans
            WHERE merchant_id = :merchant_id
            ORDER BY scan_date DESC, item_name
            LIMIT 50
            """,
        )
    return (
        "udhaar",
        """
        SELECT customer_name, amount, type, entry_date
        FROM udhaar
        WHERE merchant_id = :merchant_id
        ORDER BY entry_date DESC, id DESC
        LIMIT 50
        """,
    )


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
    return bool(table_matches) and all(table in {"udhaar", "inventory_scans"} for table in table_matches)


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
        return {
            "customer_name": str(row["customer_name"]).strip(),
            "amount": float(row["amount"]),
            "type": row.get("type", "debit") if row.get("type") in {"debit", "credit"} else "debit",
            "entry_date": date.fromisoformat(str(row["entry_date"])[:10]).isoformat(),
        }
    except (KeyError, TypeError, ValueError):
        return None


def _clean_inventory(row: dict) -> dict | None:
    try:
        return {
            "item_name": str(row["item_name"]).strip(),
            "quantity": float(row["quantity"]),
            "unit": str(row.get("unit", "units")).strip() or "units",
            "scan_date": date.fromisoformat(str(row["scan_date"])[:10]).isoformat(),
        }
    except (KeyError, TypeError, ValueError):
        return None


def _remove_masked_customers(rows: list[dict]) -> list[dict]:
    return [row for row in rows if "[CUSTOMER_NAME]" not in row.get("customer_name", "")]


def _json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found")
    return text[start : end + 1]
