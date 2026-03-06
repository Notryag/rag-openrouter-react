import { useEffect, useEffectEvent, useState } from "react";
import {
  createChatSession,
  listChatSessions,
  loadSessionConversation,
  loginUser,
  logoutUser,
  registerUser,
  restoreAuthUser,
  runIngestJob,
  sendChatMessage,
} from "../services/chatWorkspaceService";

const STARTER_PROMPTS = [
  "Summarize the three most important themes in this knowledge base.",
  "Give me an onboarding checklist based on the indexed documents.",
  "List the key risks, limitations, and caveats mentioned in the docs.",
];

function makeStatus(message, tone = "idle") {
  return { message, tone };
}

export function useChatWorkspace() {
  const [draft, setDraft] = useState("");
  const [status, setStatus] = useState(makeStatus("Ready to start."));
  const [authForm, setAuthForm] = useState({ username: "", password: "" });
  const [authUser, setAuthUser] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [conversation, setConversation] = useState([]);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);

  const openSession = useEffectEvent(async (sessionId, announce = true) => {
    const nextConversation = await loadSessionConversation(sessionId);
    setActiveSessionId(sessionId);
    setConversation(nextConversation);
    setSources([]);
    if (announce) {
      setStatus(makeStatus("Session loaded.", "success"));
    }
  });

  const handleOpenSession = async (sessionId) => {
    try {
      await openSession(sessionId);
    } catch (error) {
      setStatus(makeStatus(`Failed to load session: ${error.message}`, "error"));
    }
  };

  const refreshSessions = useEffectEvent(async (preferredSessionId = null) => {
    const rows = await listChatSessions();
    setSessions(rows);

    const fallbackId = preferredSessionId ?? activeSessionId ?? rows[0]?.id ?? null;
    if (fallbackId && rows.some((row) => row.id === fallbackId)) {
      await openSession(fallbackId, false);
      return;
    }

    setActiveSessionId(null);
    setConversation([]);
    setSources([]);
  });

  const bootstrap = useEffectEvent(async () => {
    const user = await restoreAuthUser();
    if (!user) {
      return;
    }
    setAuthUser(user);
    setStatus(makeStatus(`Signed in as ${user.username}.`, "success"));
    await refreshSessions();
  });

  useEffect(() => {
    bootstrap();
  }, []);

  const updateAuthField = (field, value) => {
    setAuthForm((current) => ({ ...current, [field]: value }));
  };

  const handleRegister = async () => {
    const username = authForm.username.trim();
    if (!username || !authForm.password.trim()) {
      setStatus(makeStatus("Username and password are required.", "error"));
      return;
    }
    try {
      await registerUser(username, authForm.password);
      setStatus(makeStatus("Registered successfully. Please sign in.", "success"));
    } catch (error) {
      setStatus(makeStatus(`Register failed: ${error.message}`, "error"));
    }
  };

  const handleLogin = async () => {
    const username = authForm.username.trim();
    if (!username || !authForm.password.trim()) {
      setStatus(makeStatus("Username and password are required.", "error"));
      return;
    }
    try {
      const result = await loginUser(username, authForm.password);
      setAuthUser({ username: result.username });
      setStatus(makeStatus(`Signed in as ${result.username}.`, "success"));
      await refreshSessions();
    } catch (error) {
      setStatus(makeStatus(`Sign-in failed: ${error.message}`, "error"));
    }
  };

  const handleLogout = () => {
    logoutUser();
    setAuthUser(null);
    setSessions([]);
    setActiveSessionId(null);
    setConversation([]);
    setSources([]);
    setStatus(makeStatus("Signed out."));
  };

  const handleCreateSession = async () => {
    try {
      const created = await createChatSession("New chat");
      await refreshSessions(created.id);
      setStatus(makeStatus("Created a new session.", "success"));
    } catch (error) {
      setStatus(makeStatus(`Create session failed: ${error.message}`, "error"));
    }
  };

  const handleIngest = async () => {
    setIngesting(true);
    setStatus(makeStatus("Preparing ingestion...", "busy"));
    try {
      const result = await runIngestJob((message, tone) => setStatus(makeStatus(message, tone)));
      setStatus(makeStatus(result, "success"));
    } catch (error) {
      setStatus(makeStatus(`Ingest failed: ${error.message}`, "error"));
    } finally {
      setIngesting(false);
    }
  };

  const handleSend = async () => {
    const question = draft.trim();
    if (!question) {
      setStatus(makeStatus("Enter a question first.", "error"));
      return;
    }

    const pendingId = Date.now();
    setDraft("");
    setLoading(true);
    setSources([]);
    setStatus(makeStatus("Generating a response...", "busy"));
    setConversation((current) => [
      ...current,
      { id: `pending-user-${pendingId}`, role: "user", content: question, pending: true },
      { id: `pending-assistant-${pendingId}`, role: "assistant", content: "", pending: true },
    ]);

    try {
      const result = await sendChatMessage(question, activeSessionId);
      setSources(result.sources || []);

      if (authUser && result.session_id) {
        await refreshSessions(result.session_id);
      } else {
        setConversation((current) => [
          ...current.filter((item) => !item.pending),
          { id: `user-${pendingId}`, role: "user", content: question },
          { id: `assistant-${pendingId}`, role: "assistant", content: result.answer || "No answer returned." },
        ]);
      }

      setStatus(makeStatus("Response ready.", "success"));
    } catch (error) {
      setDraft(question);
      setConversation((current) => current.filter((item) => !item.pending));
      setStatus(makeStatus(`Chat failed: ${error.message}`, "error"));
    } finally {
      setLoading(false);
    }
  };

  return {
    activeSession: sessions.find((session) => session.id === activeSessionId) || null,
    activeSessionId,
    authForm,
    authUser,
    conversation,
    draft,
    ingesting,
    loading,
    sessions,
    sources,
    starterPrompts: STARTER_PROMPTS,
    status,
    actions: {
      createSession: handleCreateSession,
      ingest: handleIngest,
      login: handleLogin,
      logout: handleLogout,
      openSession: handleOpenSession,
      register: handleRegister,
      send: handleSend,
      setDraft,
      setPrompt: setDraft,
      updateAuthField,
    },
  };
}
