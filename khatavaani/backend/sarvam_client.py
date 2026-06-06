"""Sarvam AI integration wrappers with hackathon-safe fallbacks.

Set SARVAM_API_KEY in khatavaani/backend/.env to enable live API calls.
Without a key, these helpers return deterministic demo outputs so the local
flow can still be tested end-to-end.
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):
        return False


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent.parent / ".env")
load_dotenv(BASE_DIR / ".env")

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "").strip()


PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?(?:0[\s-]?)?[6-9](?:[\s-]?\d){9}(?!\d)")
UPI_PATTERN = re.compile(r"\b[\w.-]+@[\w.-]+\b")


def _client():
    if not SARVAM_API_KEY:
        return None

    try:
        from sarvamai import SarvamAI
    except ImportError:
        return None

    return SarvamAI(api_subscription_key=SARVAM_API_KEY)


def strip_customer_pii(text: str) -> str:
    text = PHONE_PATTERN.sub("[PHONE_MASKED]", text or "")
    return UPI_PATTERN.sub("[UPI_MASKED]", text)


def redact_likely_customer_names(text: str) -> str:
    """Mask likely udhaar customer names before OCR text is sent to an LLM."""

    redacted_lines: list[str] = []
    for line in (text or "").splitlines():
        redacted_lines.append(
            re.sub(
                r"(\b20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}\s+)([A-Za-zÀ-ſऀ-ॿ][\wÀ-ſऀ-ॿ .-]{1,40}?)(\s+(?:debit|credit|paid|jama|udhaar|₹|rs\b))",
                r"\1[CUSTOMER_NAME]\3",
                line,
                flags=re.I,
            )
        )
    return "\n".join(redacted_lines)


def vision_ocr(file_obj, language_code: str = "auto") -> str:
    """Extract notebook text using Sarvam Vision when configured.

    Pass language_code="auto" (the default) to let Sarvam auto-detect the
    script in the image. This supports all Indian languages — Hindi, Gujarati,
    Marathi, Tamil, Telugu, Kannada, Bengali, Odia, Punjabi, and mixed scripts.
    Pass a specific BCP-47 code (e.g. "hi-IN") only if the caller is certain
    of the image language.
    """

    client = _client()
    if client is None:
        return _demo_ocr_text()

    suffix = Path(getattr(file_obj, "filename", "") or "scan.jpg").suffix or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        file_obj.seek(0)
        tmp.write(file_obj.read())
        tmp_path = tmp.name

    try:
        # Omit 'language' when auto-detecting so Sarvam's multilingual OCR
        # engine picks the right script automatically.
        job_kwargs: dict = {"output_format": "md"}
        if language_code and language_code.lower() != "auto":
            job_kwargs["language"] = language_code

        job = client.document_intelligence.create_job(**job_kwargs)
        job.upload_file(tmp_path)
        job.start()
        status = job.wait_until_complete()
        if getattr(status, "job_state", "").lower() not in {"completed", "success", "succeeded"}:
            return _demo_ocr_text()
        return _download_document_text(job)
    except Exception:
        return _demo_ocr_text()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def llm(system_prompt: str, user_prompt: str, *, temperature: float = 0.1) -> str:
    client = _client()
    if client is None:
        return ""

    try:
        response = client.chat.completions(
            model="sarvam-105b",
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return _extract_message_content(response)
    except Exception:
        return ""


def stt(audio_file, language_code: str = "auto") -> dict:
    """Transcribe audio using Sarvam saaras:v3.

    Accepts any file-like object (Flask FileStorage, BytesIO, etc.).
    The Sarvam SDK expects the file argument as a (filename, bytes, mimetype)
    tuple — passing a raw file object causes silent failures.
    """
    client = _client()
    if client is None:
        return {"transcript": "", "language_code": "hi-IN"}

    try:
        # Read raw bytes from whatever file-like object was passed in.
        audio_file.seek(0)
        audio_bytes = audio_file.read()

        # Determine filename and MIME type from the object if available.
        filename = getattr(audio_file, "filename", None) or getattr(audio_file, "name", None) or "audio.webm"
        content_type = getattr(audio_file, "content_type", None) or getattr(audio_file, "mimetype", None) or "audio/webm"

        # Sarvam SDK expects a (filename, bytes, mimetype) tuple for the file parameter.
        file_tuple = (filename, audio_bytes, content_type)

        kwargs: dict = {"file": file_tuple, "model": "saaras:v3", "mode": "transcribe"}
        # Omit language_code when "auto" so Sarvam auto-detects the spoken language.
        if language_code and language_code.lower() != "auto":
            kwargs["language_code"] = language_code

        response = client.speech_to_text.transcribe(**kwargs)
        return {
            "transcript": _get_attr(response, "transcript", ""),
            "language_code": _get_attr(response, "language_code", "hi-IN") or "hi-IN",
        }
    except Exception as exc:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        print(f"[sarvam_client] stt() failed: {exc}")
        return {"transcript": "", "language_code": "hi-IN"}


def tts(text: str, target_lang: str = "hi-IN") -> bytes:
    client = _client()
    if client is None:
        return b""

    try:
        response = client.text_to_speech.convert(
            text=text[:2500],
            target_language_code=target_lang,
            model="bulbul:v3",
            speaker="shubh",
            output_audio_codec="mp3",
        )
        return _extract_audio_bytes(response)
    except Exception:
        return b""


def translate_to(text: str, target_lang: str, source_lang: str = "en-IN") -> str:
    if target_lang == source_lang:
        return text

    client = _client()
    if client is None:
        return f"[{target_lang}] {text}"

    try:
        response = client.text.translate(
            input=text,
            source_language_code=source_lang,
            target_language_code=target_lang,
        )
        return _get_attr(response, "translated_text", "") or _get_attr(response, "output", "") or str(response)
    except Exception:
        return f"[{target_lang}] {text}"


def _download_document_text(job) -> str:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "sarvam_output.zip"
        job.download_output(str(output_path))
        chunks: list[str] = []
        with zipfile.ZipFile(output_path) as archive:
            for name in archive.namelist():
                if name.endswith((".md", ".txt", ".json")):
                    data = archive.read(name).decode("utf-8", errors="ignore")
                    if name.endswith(".json"):
                        chunks.append(_json_text(data))
                    else:
                        chunks.append(data)
        return "\n".join(chunk for chunk in chunks if chunk).strip()


def _json_text(data: str) -> str:
    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        return data

    values: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in {"text", "markdown", "content"} and isinstance(value, str):
                    values.append(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return "\n".join(values)


def _extract_message_content(response) -> str:
    if isinstance(response, dict):
        return response.get("choices", [{}])[0].get("message", {}).get("content", "")
    choices = getattr(response, "choices", None) or []
    if not choices:
        return ""
    message = getattr(choices[0], "message", None)
    return _get_attr(message, "content", "")


def _extract_audio_bytes(response) -> bytes:
    if isinstance(response, bytes):
        return response
    if isinstance(response, str):
        return base64.b64decode(response)
    if isinstance(response, dict):
        for key in ("audio", "audios", "data"):
            value = response.get(key)
            if isinstance(value, str):
                return base64.b64decode(value)
            if isinstance(value, list) and value and isinstance(value[0], str):
                return base64.b64decode(value[0])
    for key in ("audio", "audios", "data"):
        value = getattr(response, key, None)
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return base64.b64decode(value)
        if isinstance(value, list) and value and isinstance(value[0], str):
            return base64.b64decode(value[0])
    if hasattr(response, "read"):
        return response.read()
    if isinstance(response, io.BytesIO):
        return response.getvalue()
    return b""


def _get_attr(obj, key: str, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _demo_ocr_text() -> str:
    return """
    2026-06-01 Ramesh debit ₹500
    2026-06-02 Sita credit ₹200
    2026-06-01 Parle-G qty 20
    2026-06-05 Parle-G qty 8
    2026-06-01 Amul Milk qty 30
    2026-06-05 Amul Milk qty 18
    """.strip()
