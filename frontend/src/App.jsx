import { useState } from "react";
import { chat, ingest } from "./api";
import "./App.css";

export default function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const handleIngest = async () => {
    setStatus("Indexing data/...");
    setAnswer("");
    setSources([]);
    try {
      const result = await ingest(true);
      const failed = result.failed?.length ? `, failed: ${result.failed.length}` : "";
      setStatus(`Indexed ${result.files} files, ${result.chunks} chunks${failed}.`);
    } catch (err) {
      setStatus(`Ingest failed: ${err.message}`);
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
      const result = await chat(question);
      setAnswer(result.answer || "");
      setSources(result.sources || []);
      setStatus("Ready.");
    } catch (err) {
      setStatus(`Chat failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const statusTone = status.startsWith("Ingest failed") || status.startsWith("Chat failed")
    ? "error"
    : status === "Thinking..." || status.startsWith("Indexing")
      ? "busy"
      : status === "Ready."
        ? "success"
        : "idle";

  return (
    <div className="page">
      <header className="hero reveal">
        <p className="eyebrow">Retrieval-Augmented Generation</p>
        <h1>RAG Console</h1>
        <p className="subtitle">Local files -&gt; Chroma -&gt; OpenRouter</p>
      </header>

      <main className="layout">
        <section className="panel reveal delay-1">
          <div className="actionRow">
            <button className="btn secondary" onClick={handleIngest}>
              Ingest data/
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
        </section>

        <section className="panel reveal delay-2">
          <div className="panelHead">
            <h2>Answer</h2>
            <span className="count">{sources.length} sources</span>
          </div>
          <div className="answer">{answer || "No answer yet."}</div>
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
