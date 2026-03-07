import {
  chat,
  clearToken,
  createSession,
  getIngestJob,
  getSessionMessages,
  getToken,
  listSessions,
  login,
  me,
  register,
  startIngestJob,
} from "../api";

function toMessagePair(row, index) {
  return [
    {
      id: `q-${row.created_at || index}`,
      role: "user",
      content: row.question,
      createdAt: row.created_at || null,
    },
    {
      id: `a-${row.created_at || index}`,
      role: "assistant",
      content: row.answer,
      createdAt: row.created_at || null,
    },
  ];
}

export function mapSessionRowsToConversation(rows) {
  return rows.flatMap(toMessagePair);
}

export async function restoreAuthUser() {
  if (!getToken()) {
    return null;
  }
  try {
    return await me();
  } catch {
    clearToken();
    return null;
  }
}

export async function listChatSessions() {
  return listSessions();
}

export async function loadSessionConversation(sessionId) {
  const rows = await getSessionMessages(sessionId);
  return mapSessionRowsToConversation(rows);
}

export async function registerUser(username, password) {
  return register(username, password);
}

export async function loginUser(username, password) {
  return login(username, password);
}

export function logoutUser() {
  clearToken();
}

export async function createChatSession(title = "New chat") {
  return createSession(title);
}

export async function sendChatMessage(question, sessionId) {
  return chat(question, 3, sessionId);
}

export async function runIngestJob(messages, onProgress) {
  const createdJob = await startIngestJob(true);
  onProgress(messages.ingestQueued(createdJob.id), "busy");

  const deadline = Date.now() + 3 * 60 * 1000;
  while (Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    const job = await getIngestJob(createdJob.id);
    if (job.status === "queued" || job.status === "running") {
      onProgress(messages.ingestRunning(job.id, job.status), "busy");
      continue;
    }
    if (job.status === "succeeded") {
      return messages.ingestSucceeded(job.files, job.chunks, job.failed?.length || 0);
    }
    throw new Error(messages.ingestFailed(job.error || messages.ingestJobFailed));
  }

  throw new Error(messages.ingestTimedOut);
}
