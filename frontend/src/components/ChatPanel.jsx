import { usePinnedAutoScroll } from "../hooks/usePinnedAutoScroll.js";
import { useLocale } from "../hooks/useLocale.js";

function SourceList({ copy, sources }) {
  if (!sources.length) {
    return (
      <div className="sourceEmpty">
        <p>{copy.emptySources}</p>
      </div>
    );
  }

  return (
    <div className="sourceList">
      {sources.map((source, index) => (
        <article key={`${source.source || "source"}-${index}`} className="sourceCard">
          <strong>{source.source || copy.unknownSource}</strong>
          <span>{source.page !== undefined ? copy.page(source.page) : copy.retrievedChunk}</span>
        </article>
      ))}
    </div>
  );
}

function MessageThread({ conversation, copy, loading, onPickPrompt, starterPrompts }) {
  const scrollKey = `${loading ? "loading" : "idle"}:${conversation
    .map((item) => `${item.id}:${item.pending ? "pending" : "ready"}`)
    .join("|")}`;
  const { containerRef, endRef, handleScroll } = usePinnedAutoScroll(scrollKey);

  if (!conversation.length) {
    return (
      <section className="threadEmpty">
        <div className="threadLead">
          <p className="threadEyebrow">{copy.emptyEyebrow}</p>
          <h2>{copy.emptyTitle}</h2>
          <p>{copy.emptyDescription}</p>
        </div>
        <div className="promptGrid">
          {starterPrompts.map((prompt, index) => (
            <button key={prompt} className="promptCard" onClick={() => onPickPrompt(prompt)}>
              <span className="promptIndex">{copy.promptLabel(index)}</span>
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
            <span>{item.role === "user" ? copy.userRole : copy.assistantRole}</span>
            <small>{item.pending ? copy.processing : copy.logged}</small>
          </div>
          <div className="messageBody">
            {item.pending && item.role === "assistant" ? <span className="typingDots" /> : item.content}
          </div>
        </article>
      ))}
      {loading ? <div className="threadHint">{copy.waiting}</div> : null}
      <div ref={endRef} className="messageListEnd" aria-hidden="true" />
    </section>
  );
}

function Composer({ copy, draft, loading, onChange, onSend }) {
  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      onSend();
    }
  };

  return (
    <section className="composer">
      <div className="composerMeta">
        <p className="chatKicker">{copy.composerTitle}</p>
        <p className="composerHint">{copy.composerHint}</p>
      </div>
      <textarea
        className="composerInput"
        value={draft}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={copy.composerPlaceholder}
        rows={4}
      />
      <button className="button primary composerButton" onClick={onSend} disabled={loading}>
        {loading ? copy.sendLoading : copy.send}
      </button>
    </section>
  );
}

export default function ChatPanel({ workspace }) {
  const { activeSession, authUser, conversation, draft, loading, sources, starterPrompts } = workspace;
  const { send, setDraft, setPrompt } = workspace.actions;
  const questionCount = conversation.filter((item) => item.role === "user").length;
  const { copy } = useLocale();
  const chatCopy = copy.chat;
  const sessionTitle =
    activeSession?.title === "New chat" ? copy.sidebar.newChatTitle : activeSession?.title || chatCopy.unsavedTitle;

  return (
    <main className="chatStage">
      <header className="chatHeader">
        <div>
          <p className="chatKicker">{chatCopy.headerKicker}</p>
          <h2>{sessionTitle}</h2>
          <p className="chatText">
            {authUser ? chatCopy.accountDescription : chatCopy.guestDescription}
          </p>
        </div>
        <div className="chatStats">
          <div>
            <p className="metricLabel">{chatCopy.questionCount}</p>
            <strong>{questionCount}</strong>
          </div>
          <div>
            <p className="metricLabel">{chatCopy.sourceCount}</p>
            <strong>{sources.length}</strong>
          </div>
          <div>
            <p className="metricLabel">{chatCopy.mode}</p>
            <strong>{authUser ? chatCopy.linkedMode : chatCopy.guestMode}</strong>
          </div>
        </div>
      </header>

      <section className="tickerRow">
        <p className="tickerLabel">{chatCopy.liveDesk}</p>
        <div className="tickerStrip">
          <div className={`tickerChip ${loading ? "live" : ""}`}>
            <span className="tickerDot" />
            <span>{loading ? chatCopy.modelBusy : chatCopy.ready}</span>
          </div>
          <div className="tickerChip">
            <span className="tickerDot" />
            <span>{activeSession ? chatCopy.sessionLabel(activeSession.id) : chatCopy.noSession}</span>
          </div>
        </div>
      </section>

      <MessageThread
        conversation={conversation}
        copy={chatCopy}
        loading={loading}
        onPickPrompt={setPrompt}
        starterPrompts={starterPrompts}
      />

      <Composer copy={chatCopy} draft={draft} loading={loading} onChange={setDraft} onSend={send} />

      <section className="inspector">
        <div className="inspectorHeader">
          <div>
            <p className="chatKicker">{chatCopy.inspectorKicker}</p>
            <h3>{chatCopy.inspectorTitle}</h3>
          </div>
          <p className="sourceMeta">
            {sources.length ? chatCopy.citationCount(sources.length) : chatCopy.awaitingRetrieval}
          </p>
        </div>
        <SourceList copy={chatCopy} sources={sources} />
      </section>
    </main>
  );
}
