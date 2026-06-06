import axios from "axios";

const api = axios.create({
  baseURL: process.env.REACT_APP_KHATAVAANI_API_BASE || "http://localhost:5000",
  headers: {
    "X-Merchant-ID": "demo_merchant_001",
    "X-Lang-Preference": "hi-IN",
  },
});

export async function scanKhata(imageFile) {
  const body = new FormData();
  body.append("image", imageFile);
  const { data } = await api.post("/api/scan", body, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return privacyFilter(data);
}

export async function getVelocity() {
  const { data } = await api.get("/api/velocity");
  return data;
}

export async function askKhata(audioBlob, transcript = "") {
  const body = new FormData();
  if (audioBlob) {
    body.append("audio", audioBlob, "question.webm");
  }
  if (transcript) {
    body.append("transcript", transcript);
  }

  const response = await api.post("/api/ask", body, {
    headers: { "Content-Type": "multipart/form-data" },
    responseType: "blob",
  });

  const audioUrl = response.data?.size ? URL.createObjectURL(response.data) : "";
  return {
    audioUrl,
    transcript: decodeHeader(response.headers["x-transcript"]),
    answerText: decodeHeader(response.headers["x-answer-text"]),
    agent: response.headers["x-agent"],
    langDetected: response.headers["x-lang-detected"],
  };
}

function decodeHeader(value = "") {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

function privacyFilter(payload) {
  const text = JSON.stringify(payload)
    .replace(/(?:\+?91[\s-]?)?(?:0[\s-]?)?[6-9](?:[\s-]?\d){9}/g, "[PHONE_MASKED]")
    .replace(/\b[\w.-]+@[\w.-]+\b/g, "[UPI_MASKED]");
  return JSON.parse(text);
}
