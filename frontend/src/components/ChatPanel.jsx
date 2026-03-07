import { usePinnedAutoScroll } from "../hooks/usePinnedAutoScroll.js";

function SourceList({ sources }) {
  if (!sources.length) {
    return (
      <div className="sourceEmpty">
        <p>No citations are shown yet. Ask a new question to inspect the retrieved documents here.</p>
      </div>
    );
  }

  return (
    <div className="sourceList">
      {sources.map((source, index) => (
        <article key={`${source.source || "source"}-${index}`} className="sourceCard">
          <strong>{source.source || "Unknown source"}</strong>
          <span>{source.page !== undefined ? `page ${source.page}` : "retrieved chunk"}</span>
        </article>
      ))}
    </div>
  );
}

function MessageThread({ conversation, loading, onPickPrompt, starterPrompts }) {
  const scrollKey = `${loading ? "loading" : "idle"}:${conversation
    .map((item) => `${item.id}:${item.pending ? "pending" : "ready"}`)
    .join("|")}`;
  const { containerRef, endRef, handleScroll } = usePinnedAutoScroll(scrollKey);

  if (!conversation.length) {
    return (
      <section className="threadEmpty">
        <div className="threadLead">
          <p className="threadEyebrow">Issue 01 / Brief</p>
          <h2>Ask against the indexed archive</h2>
          <p>Start with a pointed question, then inspect the reply and the supporting citations in the same working surface.</p>
        </div>
        <div className="promptGrid">
          {starterPrompts.map((prompt, index) => (
            <button key={prompt} className="promptCard" onClick={() => onPickPrompt(prompt)}>
              <span className="promptIndex">Prompt {String(index + 1).padStart(2, "0")}</span>
              <span className="promptText">{prompt}</span>
            </button>
          ))}
        </div>
      </section>
    );
  }

  return (
    <section ref={containerRef} className="messageList" onScroll={handleScroll}>
      {conversation.map((item) => (
        <article key={item.id} className={`messageBubble ${item.role}`}>
          <div className="messageMeta">
            <span>{item.role === "user" ? "Operator" : "System"}</span>
            <small>{item.pending ? "Processing" : "Logged"}</small>
          </div>
          <div className="messageBody">
            {item.pending && item.role === "assistant" ? <span className="typingDots" /> : item.content}
          </div>
        </article>
      ))}
      {loading ? <div className="threadHint">Waiting for the model to finish the current reply...</div> : null}
      <div ref={endRef} className="messageListEnd" aria-hidden="true" />
    </section>
  );
}

function Composer({ draft, loading, onChange, onSend }) {
  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      onSend();
    }
  };

  return (
    <section className="composer">
      <div className="composerMeta">
        <p className="chatKicker">Prompt Draft</p>
        <p className="composerHint">Enter sends / Shift+Enter adds a new line</p>
      </div>
      <textarea
        className="composerInput"
        value={draft}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Draft a precise question about the indexed files and send it to the retrieval desk."
        rows={4}
      />
      <button className="button primary composerButton" onClick={onSend} disabled={loading}>
        {loading ? "Dispatching..." : "Dispatch"}
      </button>
    </section>
  );
}

export default function ChatPanel({ workspace }) {
  const { activeSession, authUser, conversation, draft, loading, sources, starterPrompts } = workspace;
  const { send, setDraft, setPrompt } = workspace.actions;
  const questionCount = conversation.filter((item) => item.role === "user").length;

  return (
    <main className="chatStage">
      <header className="chatHeader">
        <div>
          <p className="chatKicker">Transcript Desk</p>
          <h2>{activeSession?.title || "Unsaved dispatch"}</h2>
          <p className="chatText">
            {authUser ? "Messages sync into the selected account ledger and remain available for later review." : "Guest mode can ask immediately, but the transcript disappears after reload."}
          </p>
        </div>
        <div className="chatStats">
          <div>
            <p className="metricLabel">Questions</p>
            <strong>{questionCount}</strong>
          </div>
          <div>
            <p className="metricLabel">Sources</p>
            <strong>{sources.length}</strong>
          </div>
          <div>
            <p className="metricLabel">Mode</p>
            <strong>{authUser ? "Linked" : "Guest"}</strong>
          </div>
        </div>
      </header>

      <section className="tickerRow">
        <p className="tickerLabel">Live desk</p>
        <div className="tickerStrip">
          <div className={`tickerChip ${loading ? "live" : ""}`}>
            <span className="tickerDot" />
            <span>{loading ? "Model busy" : "Ready for prompt"}</span>
          </div>
          <div className="tickerChip">
            <span className="tickerDot" />
            <span>{activeSession ? `Session #${activeSession.id}` : "No saved session"}</span>
          </div>
        </div>
      </section>

      <MessageThread
        conversation={conversation}
        loading={loading}
        onPickPrompt={setPrompt}
        starterPrompts={starterPrompts}
      />

      <Composer draft={draft} loading={loading} onChange={setDraft} onSend={send} />

      <section className="inspector">
        <div className="inspectorHeader">
          <div>
            <p className="chatKicker">Evidence ledger</p>
            <h3>Sources for the latest reply</h3>
          </div>
          <p className="sourceMeta">{sources.length ? `${sources.length} citation${sources.length === 1 ? "" : "s"}` : "Awaiting retrieval"}</p>
        </div>
        <SourceList sources={sources} />
      </section>
    </main>
  );
}
