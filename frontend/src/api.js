import { getLocale, getMessages } from "./state/localeMessages.js";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const TOKEN_KEY = "rag_access_token";

function getAuthHeaders() {
  const token = localStorage.getItem(TOKEN_KEY);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function formatValidationError(item) {
  const apiCopy = getMessages(getLocale()).api;
  const field = item?.loc?.[item.loc.length - 1];
  const fieldLabel = apiCopy.fieldLabels[field] || apiCopy.fieldFallback;

  if (item?.type === "string_too_short" && item?.ctx?.min_length) {
    return apiCopy.tooShort(fieldLabel, item.ctx.min_length);
  }

  if (item?.type === "string_too_long" && item?.ctx?.max_length) {
    return apiCopy.tooLong(fieldLabel, item.ctx.max_length);
  }

  return item?.msg || apiCopy.invalidInput;
}

function formatErrorDetail(detail, fallback = getMessages(getLocale()).api.requestFailed) {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map(formatValidationError).join(" ");
  }

  if (detail && typeof detail === "object") {
    try {
      return JSON.stringify(detail);
    } catch {
      return fallback;
    }
  }

  return fallback;
}

async function handleResponse(res) {
  if (!res.ok) {
    const fallback = getMessages(getLocale()).api.requestFailed;
    let detail = fallback;
    try {
      const data = await res.json();
      detail = formatErrorDetail(data.detail ?? data, fallback);
    } catch {
      detail = formatErrorDetail(await res.text(), fallback);
    }
    throw new Error(formatErrorDetail(detail, fallback));
  }
  return res.json();
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export async function register(username, password) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return handleResponse(res);
}

export async function login(username, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await handleResponse(res);
  localStorage.setItem(TOKEN_KEY, data.access_token);
  return data;
}

export async function me() {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { ...getAuthHeaders() },
  });
  return handleResponse(res);
}

export async function listSessions() {
  const res = await fetch(`${API_BASE}/sessions`, {
    headers: { ...getAuthHeaders() },
  });
  return handleResponse(res);
}

export async function createSession(title = "New chat") {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ title }),
  });
  return handleResponse(res);
}

export async function getSessionMessages(sessionId) {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/messages`, {
    headers: { ...getAuthHeaders() },
  });
  return handleResponse(res);
}

export async function ingest(reset = true) {
  const res = await fetch(`${API_BASE}/ingest`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ reset }),
  });
  return handleResponse(res);
}

export async function startIngestJob(reset = true) {
  const res = await fetch(`${API_BASE}/ingest/jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ reset }),
  });
  return handleResponse(res);
}

export async function getIngestJob(jobId) {
  const res = await fetch(`${API_BASE}/ingest/jobs/${jobId}`, {
    headers: { ...getAuthHeaders() },
  });
  return handleResponse(res);
}

export async function chat(question, k = 3, sessionId = null) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ question, k, session_id: sessionId }),
  });
  return handleResponse(res);
}
