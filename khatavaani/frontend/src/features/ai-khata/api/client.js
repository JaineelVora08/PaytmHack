import axios from "axios";

import {
  mockBroadcast,
  mockGroupBuy,
  mockNewsTrends,
  mockPulse,
} from "./mocks";


export const USE_MOCK = process.env.REACT_APP_USE_MOCK !== "false";

const PHONE_PATTERN = /(?:\+?91[\s-]?)?(?:0[\s-]?)?[6-9](?:[\s-]?\d){9}/g;
const UPI_PATTERN = /\b[\w.-]+@[\w.-]+\b/g;

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || "http://localhost:5000",
  headers: {
    "X-Merchant-ID": process.env.REACT_APP_MERCHANT_ID || "demo_merchant_001",
    "X-Lang-Preference": process.env.REACT_APP_LANG_PREFERENCE || "hi-IN",
  },
});

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
