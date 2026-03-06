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
  if (!conversation.length) {
    return (
      <section className="threadEmpty">
        <p className="threadEyebrow">Start here</p>
        <h2>Turn the demo into a real chat flow</h2>
        <p>Use multi-turn conversation, saved sessions, and document citations in one focused workspace.</p>
        <div className="promptGrid">
          {starterPrompts.map((prompt) => (
            <button key={prompt} className="promptCard" onClick={() => onPickPrompt(prompt)}>
              {prompt}
            </button>
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="messageList">
      {conversation.map((item) => (
        <article key={item.id} className={`messageBubble ${item.role}`}>
          <div className="messageMeta">
            <span>{item.role === "user" ? "You" : "Assistant"}</span>
            {item.pending ? <small>Working...</small> : null}
          </div>
          <div className="messageBody">
            {item.pending && item.role === "assistant" ? <span className="typingDots" /> : item.content}
          </div>
        </article>
      ))}
      {loading ? <div className="threadHint">Waiting for the model to finish the current reply...</div> : null}
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
      <textarea
        className="composerInput"
        value={draft}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask anything about the indexed files. Enter sends, Shift+Enter inserts a newline."
        rows={4}
      />
      <button className="button primary composerButton" onClick={onSend} disabled={loading}>
        {loading ? "Sending..." : "Send"}
      </button>
    </section>
  );
}

export default function ChatPanel({ workspace }) {
  const { activeSession, authUser, conversation, draft, loading, sources, starterPrompts } = workspace;
  const { send, setDraft, setPrompt } = workspace.actions;

  return (
    <main className="chatStage">
      <header className="chatHeader">
        <div>
          <p className="chatKicker">Conversation</p>
          <h2>{activeSession?.title || "Temporary session"}</h2>
          <p className="chatText">
            {authUser ? "Messages sync into the selected account session." : "Guest mode can ask immediately, but messages disappear after reload."}
          </p>
        </div>
        <div className="chatStats">
          <div>
            <strong>{conversation.filter((item) => item.role === "user").length}</strong>
            <span>questions</span>
          </div>
          <div>
            <strong>{sources.length}</strong>
            <span>sources</span>
          </div>
        </div>
      </header>

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
            <p className="chatKicker">References</p>
            <h3>Sources for the latest reply</h3>
          </div>
        </div>
        <SourceList sources={sources} />
      </section>
    </main>
  );
}
