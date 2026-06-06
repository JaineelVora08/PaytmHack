import axios from "axios";

import {
  mockBroadcast,
  mockGroupBuy,
  mockNewsTrends,
  mockPulse,
} from "./mocks";

const _env = typeof process !== "undefined" && process?.env ? process.env : import.meta.env;
// Default to mock=true so the page never goes blank when backend is not running.
// Set REACT_APP_USE_MOCK=false (or VITE_REACT_APP_USE_MOCK=false) to use live backend.
export const USE_MOCK = (_env.REACT_APP_USE_MOCK ?? _env.VITE_REACT_APP_USE_MOCK ?? "true") !== "false";

const PHONE_PATTERN = /(?:\+?91[\s-]?)?(?:0[\s-]?)?[6-9](?:[\s-]?\d){9}/g;
// Narrow UPI pattern: only match recognised UPI handle formats (name@upi, phone@bank etc)
const UPI_PATTERN = /\b[\w.+-]{3,}@(?:upi|paytm|oksbi|okaxis|okhdfcbank|okicici|ybl|ibl|axl|apl|barodampay|pnb|aubank|kotak|freecharge|phonepe)\b/gi;

const api = axios.create({
  baseURL:
    _env.REACT_APP_KHATAVAANI_API_BASE || _env.REACT_APP_API_BASE_URL || _env.VITE_REACT_APP_KHATAVAANI_API_BASE || _env.VITE_REACT_APP_API_BASE_URL ||
    "http://localhost:5000",
  headers: {
    "X-Merchant-ID": _env.REACT_APP_MERCHANT_ID || _env.VITE_REACT_APP_MERCHANT_ID || "demo_merchant_001",
    "X-Lang-Preference": _env.REACT_APP_LANG_PREFERENCE || _env.VITE_REACT_APP_LANG_PREFERENCE || "hi-IN",
  },
});

export async function scanKhata(imageFile) {
  const body = new FormData();
  body.append("image", imageFile);
  const { data } = await api.post("/api/scan", body, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return stripPII(data);
}

export async function getVelocity() {
  const { data } = await api.get("/api/velocity");
  return stripPII(data);
}

export async function getLocalRecords() {
  const { data } = await api.get("/api/records");
  return stripPII(data);
}

export async function askKhata(audioBlob, transcript = "") {
  const body = new FormData();
  if (audioBlob) {
    body.append("audio", audioBlob, audioFilename(audioBlob.type));
  }
  if (transcript) {
    body.append("transcript", transcript);
  }

  const response = await api.post("/api/ask", body, {
    headers: { "Content-Type": "multipart/form-data" },
    responseType: "blob",
  });

  const audioUrl = response.data?.size ? URL.createObjectURL(response.data) : "";
  return stripPII({
    audioUrl,
    transcript: decodeHeader(response.headers["x-transcript"]),
    answerText: decodeHeader(response.headers["x-answer-text"]),
    agent: response.headers["x-agent"],
    langDetected: response.headers["x-lang-detected"],
  });
}

function audioFilename(type = "") {
  const mime = type.split(";", 1)[0].toLowerCase();
  if (mime === "audio/mp4") {
    return "question.m4a";
  }
  if (mime === "audio/ogg" || mime === "audio/opus") {
    return "question.ogg";
  }
  if (mime === "audio/wav") {
    return "question.wav";
  }
  return "question.webm";
}

export async function getPulse() {
  if (USE_MOCK) {
    return stripPII(mockPulse);
  }

  const response = await api.get("/api/pulse");
  return stripPII(response.data);
}

export async function getNewsTrends(region = "urban_mumbai") {
  if (USE_MOCK) {
    return stripPII(mockNewsTrends);
  }

  const response = await api.get("/api/news-trends", {
    params: { region },
  });
  return stripPII(response.data);
}

export async function getGroupBuy() {
  if (USE_MOCK) {
    return stripPII(mockGroupBuy);
  }

  const response = await api.get("/api/group-buy");
  return stripPII(response.data);
}

export async function sendBroadcast(payload) {
  if (USE_MOCK) {
    return stripPII({
      ...mockBroadcast,
      target_segment: payload?.target_segment,
    });
  }

  const response = await api.post("/api/broadcast", payload);
  return stripPII(response.data);
}

function decodeHeader(value = "") {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export function stripPII(value) {
  if (typeof value === "string") {
    return value.replace(PHONE_PATTERN, "[PHONE_MASKED]").replace(UPI_PATTERN, "[UPI_MASKED]");
  }

  if (Array.isArray(value)) {
    return value.map((item) => stripPII(item));
  }

  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, stripPII(item)]),
    );
  }

  return value;
}

export default api;
