import { useEffect, useEffectEvent, useState } from "react";
import { useLocale } from "./useLocale.js";
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

function makeStatus(message, tone = "idle") {
  return { message, tone };
}

export function useChatWorkspace() {
  const { copy } = useLocale();
  const statusCopy = copy.status;
  const [draft, setDraft] = useState("");
  const [status, setStatus] = useState(makeStatus(statusCopy.ready));
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
      setStatus(makeStatus(statusCopy.sessionLoaded, "success"));
    }
  });

  const handleOpenSession = async (sessionId) => {
    try {
      await openSession(sessionId);
    } catch (error) {
      setStatus(makeStatus(statusCopy.failedToLoadSession(error.message), "error"));
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
    setStatus(makeStatus(statusCopy.signedInAs(user.username), "success"));
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
      setStatus(makeStatus(statusCopy.credentialsRequired, "error"));
      return;
    }
    try {
      await registerUser(username, authForm.password);
      setStatus(makeStatus(statusCopy.registerSuccess, "success"));
    } catch (error) {
      setStatus(makeStatus(statusCopy.registerFailed(error.message), "error"));
    }
  };

  const handleLogin = async () => {
    const username = authForm.username.trim();
    if (!username || !authForm.password.trim()) {
      setStatus(makeStatus(statusCopy.credentialsRequired, "error"));
      return;
    }
    try {
      const result = await loginUser(username, authForm.password);
      setAuthUser({ username: result.username });
      setStatus(makeStatus(statusCopy.signedInAs(result.username), "success"));
      await refreshSessions();
    } catch (error) {
      setStatus(makeStatus(statusCopy.signInFailed(error.message), "error"));
    }
  };

  const handleLogout = () => {
    logoutUser();
    setAuthUser(null);
    setSessions([]);
    setActiveSessionId(null);
    setConversation([]);
    setSources([]);
    setStatus(makeStatus(statusCopy.signedOut));
  };

  const handleCreateSession = async () => {
    try {
      const created = await createChatSession(copy.sidebar.newChatTitle);
      await refreshSessions(created.id);
      setStatus(makeStatus(statusCopy.createdSession, "success"));
    } catch (error) {
      setStatus(makeStatus(statusCopy.createSessionFailed(error.message), "error"));
    }
  };

  const handleIngest = async () => {
    setIngesting(true);
    setStatus(makeStatus(statusCopy.preparingIngest, "busy"));
    try {
      const result = await runIngestJob(statusCopy, (message, tone) => setStatus(makeStatus(message, tone)));
      setStatus(makeStatus(result, "success"));
    } catch (error) {
      setStatus(makeStatus(error.message, "error"));
    } finally {
      setIngesting(false);
    }
  };

  const handleSend = async () => {
    const question = draft.trim();
    if (!question) {
      setStatus(makeStatus(statusCopy.enterQuestion, "error"));
      return;
    }

    const pendingId = Date.now();
    setDraft("");
    setLoading(true);
    setSources([]);
    setStatus(makeStatus(statusCopy.generating, "busy"));
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
          { id: `assistant-${pendingId}`, role: "assistant", content: result.answer || statusCopy.noAnswer },
        ]);
      }

      setStatus(makeStatus(statusCopy.responseReady, "success"));
    } catch (error) {
      setDraft(question);
      setConversation((current) => current.filter((item) => !item.pending));
      setStatus(makeStatus(statusCopy.chatFailed(error.message), "error"));
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
    starterPrompts: copy.chat.starterPrompts,
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
