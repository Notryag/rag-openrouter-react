import { useEffect, useState } from "react";
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
} from "./api";
import "./App.css";

export default function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [authUser, setAuthUser] = useState(null);

  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    async function bootstrap() {
      if (!getToken()) {
        return;
      }
      try {
        const user = await me();
        setAuthUser(user);
        await loadSessions();
      } catch {
        clearToken();
      }
    }
    bootstrap();
  }, []);

  const loadSessions = async () => {
    const rows = await listSessions();
    setSessions(rows);
    if (rows.length > 0 && !activeSessionId) {
      await selectSession(rows[0].id);
    }
  };

  const selectSession = async (sessionId) => {
    setActiveSessionId(sessionId);
    const rows = await getSessionMessages(sessionId);
    setMessages(rows);
    if (rows.length > 0) {
      const last = rows[rows.length - 1];
      setAnswer(last.answer);
      setStatus("Session loaded.");
    } else {
      setAnswer("");
      setStatus("Session is empty.");
    }
  };

  const handleRegister = async () => {
    if (!username.trim() || !password.trim()) {
      setStatus("Username and password are required.");
      return;
    }
    try {
      await register(username.trim(), password);
      setStatus("Registered. Please login.");
    } catch (err) {
      setStatus(`Register failed: ${err.message}`);
    }
  };

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) {
      setStatus("Username and password are required.");
      return;
    }
    try {
      const result = await login(username.trim(), password);
      setAuthUser({ username: result.username });
      setStatus(`Logged in as ${result.username}.`);
      await loadSessions();
    } catch (err) {
      setStatus(`Login failed: ${err.message}`);
    }
  };

  const handleLogout = () => {
    clearToken();
    setAuthUser(null);
    setSessions([]);
    setActiveSessionId(null);
    setMessages([]);
    setStatus("Logged out.");
  };

  const handleCreateSession = async () => {
    try {
      const created = await createSession("New chat");
      await loadSessions();
      await selectSession(created.id);
      setStatus("New session created.");
    } catch (err) {
      setStatus(`Create session failed: ${err.message}`);
    }
  };

  const handleIngest = async () => {
    setIngesting(true);
    setStatus("Queueing ingest job...");
    setAnswer("");
    setSources([]);
    try {
      const createdJob = await startIngestJob(true);
      setStatus(`Ingest job #${createdJob.id} queued...`);

      const deadline = Date.now() + 3 * 60 * 1000;
      while (Date.now() < deadline) {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        const job = await getIngestJob(createdJob.id);
        if (job.status === "queued" || job.status === "running") {
          setStatus(`Ingest job #${job.id} ${job.status}...`);
          continue;
        }
        if (job.status === "succeeded") {
          const failed = job.failed?.length ? `, failed: ${job.failed.length}` : "";
          setStatus(`Indexed ${job.files} files, ${job.chunks} chunks${failed}.`);
          return;
        }
        throw new Error(job.error || "Ingest job failed.");
      }
      throw new Error("Ingest job timed out after 3 minutes.");
    } catch (err) {
      setStatus(`Ingest failed: ${err.message}`);
    } finally {
      setIngesting(false);
    }
  };

  const handleAsk = async () => {
    if (!question.trim()) {
      setStatus("Please enter a question.");
      return;
    }
    setLoading(true);
    setStatus("Thinking...");
    try {
      const result = await chat(question, 4, activeSessionId);
      setAnswer(result.answer || "");
      setSources(result.sources || []);
      setStatus("Ready.");

      if (authUser && result.session_id) {
        setActiveSessionId(result.session_id);
        await loadSessions();
        await selectSession(result.session_id);
      }
    } catch (err) {
      setStatus(`Chat failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const statusTone = status.startsWith("Ingest failed") || status.startsWith("Chat failed") || status.startsWith("Login failed") || status.startsWith("Register failed")
    ? "error"
    : status === "Thinking..." || status.startsWith("Indexing") || status.startsWith("Ingest job") || status.startsWith("Queueing ingest job")
      ? "busy"
      : status === "Ready." || status.startsWith("Logged in") || status.startsWith("Session loaded") || status.startsWith("New session")
        ? "success"
        : "idle";

  return (
    <div className="page">
      <header className="hero reveal">
        <div className="heroTop">
          <div>
            <p className="eyebrow">Retrieval-Augmented Generation</p>
            <h1>RAG Console</h1>
            <p className="subtitle">Local files -&gt; Chroma -&gt; OpenRouter</p>
          </div>
          <div className="authCard">
            {authUser ? (
              <>
                <p className="authUser">Signed in: <strong>{authUser.username}</strong></p>
                <button className="btn secondary" onClick={handleLogout}>Logout</button>
              </>
            ) : (
              <>
                <input
                  className="authInput"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="username"
                />
                <input
                  className="authInput"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="password (min 8 chars)"
                />
                <div className="authRow">
                  <button className="btn secondary" onClick={handleRegister}>Register</button>
                  <button className="btn primary" onClick={handleLogin}>Login</button>
                </div>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="layout">
        <section className="panel reveal delay-1">
          <div className="actionRow">
            <button className="btn secondary" onClick={handleIngest} disabled={ingesting}>
              {ingesting ? "Indexing..." : "Ingest data/"}
            </button>
            <span className={`status ${statusTone}`}>{status || "Idle"}</span>
          </div>

          <label className="label" htmlFor="question">
            Question
          </label>
          <textarea
            id="question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask something about your files..."
            rows={6}
          />
          <div className="actionRow">
            <button className="btn primary" onClick={handleAsk} disabled={loading}>
              {loading ? "Working..." : "Ask"}
            </button>
          </div>

          {authUser && (
            <div className="sessionPanel">
              <div className="panelHead">
                <h3>My Sessions</h3>
                <button className="btn secondary compact" onClick={handleCreateSession}>New</button>
              </div>
              {sessions.length === 0 ? (
                <p className="emptyHint">No sessions yet. Ask your first question.</p>
              ) : (
                <ul className="sessionList">
                  {sessions.map((session) => (
                    <li key={session.id}>
                      <button
                        className={`sessionBtn ${session.id === activeSessionId ? "active" : ""}`}
                        onClick={() => selectSession(session.id)}
                      >
                        {session.title}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </section>

        <section className="panel reveal delay-2">
          <div className="panelHead">
            <h2>Answer</h2>
            <span className="count">{sources.length} sources</span>
          </div>
          <div className="answer">{answer || "No answer yet."}</div>

          {messages.length > 0 && (
            <div className="history">
              <h3>Session History</h3>
              <ul>
                {messages.map((m, idx) => (
                  <li key={`${m.created_at}-${idx}`}>
                    <p className="historyQ">Q: {m.question}</p>
                    <p className="historyA">A: {m.answer}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {sources.length > 0 && (
            <div className="sources">
              <h3>References</h3>
              <ul>
                {sources.map((src, idx) => (
                  <li key={`${src.source || "source"}-${idx}`}>
                    <span className="sourcePath">{src.source || ""}</span>
                    {src.page !== undefined ? <span className="sourceMeta">page {src.page}</span> : null}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
