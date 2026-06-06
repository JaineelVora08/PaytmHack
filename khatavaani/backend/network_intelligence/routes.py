"""Flask routes for the Network Intelligence module."""

from __future__ import annotations

from flask import Blueprint, Response, jsonify, request

try:
    from database import get_db
except ImportError:  # Phase 1 local fallback until shared file is implemented.
    get_db = None

try:
    from sarvam_client import llm, translate_to, tts
except ImportError:  # Phase 1 local fallback until Sarvam wrapper is implemented.
    tts = None

    def llm(system_prompt: str, user_prompt: str) -> str:
        return "Hi! IPL Final tomorrow - get your snacks today. 10% off on Rs 200+!"

    def translate_to(text: str, target_lang: str, source_lang: str = "en-IN") -> str:
        if target_lang == source_lang:
            return text
        return f"[{target_lang}] {text}"

try:
    from network_intelligence.broadcast import create_campaign
    from network_intelligence.network import compute_pulse, get_active_groups
    from network_intelligence.news_client import get_trends
    from network_intelligence.privacy import add_noise, k_anonymous_signal
except ImportError:
    from .broadcast import create_campaign
    from .network import compute_pulse, get_active_groups
    from .news_client import get_trends
    from .privacy import add_noise, k_anonymous_signal


network = Blueprint("network", __name__)

DEFAULT_BROADCAST_MESSAGES = {
    "en-IN": "Hi! IPL Final tomorrow - get your snacks today. 10% off on Rs 200+!",
    "hi-IN": "Namaste! Kal IPL Final hai - cold drinks aur snacks aaj hi le lo. Rs 200+ par 10% off!",
    "mr-IN": "Namaskar! Udya IPL Final aahe - cold drinks aaj gheun ja. Rs 200+ var 10% soot!",
    "gu-IN": "Namaste! Kale IPL Final chhe - cold drinks ane snacks lai jao. Rs 200+ par 10% chhut!",
    "ta-IN": "Vanakkam! Naalai IPL Final - cold drinks matrum snacks indre vaangungal. Rs 200+ ku 10% off!",
}


def _merchant_id() -> str:
    return request.headers.get("X-Merchant-ID", "demo_merchant_001")


def _lang_pref() -> str:
    return request.headers.get("X-Lang-Preference", "hi-IN")


def _region() -> str:
    if get_db is None:
        return request.args.get("region", "urban_mumbai")

    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT region FROM merchants WHERE id=?",
                (_merchant_id(),),
            ).fetchone()
    except Exception:
        row = None

    return row["region"] if row else request.args.get("region", "urban_mumbai")


@network.route("/api/pulse", methods=["GET"])
def pulse():
    pulse_data = compute_pulse(_region())

    if not k_anonymous_signal(pulse_data["merchant_count"]):
        return jsonify({"pulse": None, "reason": "insufficient_data"}), 200

    pulse_data["merchant_count"] = add_noise(pulse_data["merchant_count"])

    lang = _lang_pref()
    if lang != "en-IN":
        headline_key = f"headline_{lang.split('-')[0]}"
        if not pulse_data.get(headline_key):
            pulse_data[headline_key] = translate_to(pulse_data["headline_en"], lang, "en-IN")

    pulse_data["privacy_note"] = (
        f"Aggregated across {pulse_data['merchant_count']} merchants. "
        "+/-15% noise applied."
    )

    return jsonify({"pulse": pulse_data}), 200


@network.route("/api/pulse-audio", methods=["GET"])
def pulse_audio():
    lang = _lang_pref()
    pulse_data = compute_pulse(_region())
    text = pulse_data.get("headline_hi") if lang == "hi-IN" else pulse_data.get("headline_en")
    if lang not in {"hi-IN", "en-IN"}:
        text = translate_to(pulse_data["headline_en"], lang, "en-IN")

    audio_bytes = tts(text or pulse_data["headline_en"], lang) if tts else b""
    return Response(audio_bytes, mimetype="audio/mpeg")


@network.route("/api/news-trends", methods=["GET"])
def news_trends():
    region = request.args.get("region", _region())
    trends = get_trends(region)

    lang = _lang_pref()
    if lang != "en-IN":
        body_key = f"body_{lang.split('-')[0]}"
        for trend in trends:
            if trend.get("body_en") and not trend.get(body_key):
                trend[body_key] = translate_to(trend["body_en"], lang, "en-IN")

    return jsonify({"trends": trends}), 200


@network.route("/api/group-buy", methods=["GET"])
def group_buy():
    return jsonify({"active_groups": get_active_groups(_merchant_id())}), 200


@network.route("/api/broadcast", methods=["POST"])
def broadcast():
    body = request.get_json(silent=True) or {}
    event_id = body.get("event_id")
    if not event_id:
        return jsonify({"status": "error", "message": "event_id is required"}), 400

    target_segment = body.get("target_segment", {})
    if target_segment is None:
        target_segment = {}
    if not isinstance(target_segment, dict):
        return jsonify({"status": "error", "message": "target_segment must be an object"}), 400

    segment_id = target_segment.get("segment_id", "nearby_2km")
    languages = body.get("languages", ["hi-IN", "mr-IN", "gu-IN", "en-IN"])
    if not isinstance(languages, list) or not languages:
        return jsonify({"status": "error", "message": "languages must be a non-empty list"}), 400

    prompt = (
        f"Generate a short, friendly customer offer SMS for event: {event_id}. "
        "Max 30 words."
    )
    base_message = llm(
        "You are a marketing copywriter for Indian shops. Tone: warm, casual.",
        prompt,
    ).strip()
    if not base_message:
        base_message = DEFAULT_BROADCAST_MESSAGES["en-IN"]

    messages = {}
    for lang in languages:
        translated = base_message if lang == "en-IN" else translate_to(base_message, lang, "en-IN")
        if translated.startswith(f"[{lang}] "):
            translated = DEFAULT_BROADCAST_MESSAGES.get(lang, translated)
        messages[lang] = translated.strip() or DEFAULT_BROADCAST_MESSAGES.get(lang, base_message)

    if "en-IN" not in messages:
        messages["en-IN"] = base_message

    try:
        campaign = create_campaign(event_id, segment_id, messages)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    return jsonify(
        {
            "status": "queued",
            "messages": messages,
            "estimated_reach": campaign["estimated_reach"],
            "channel": "paytm_ads",
            "campaign_id": campaign["campaign_id"],
            "privacy_note": "No customer PII exposed. Paytm Ads handles targeting on platform side.",
        }
    ), 200
