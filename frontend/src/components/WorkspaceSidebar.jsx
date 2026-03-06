function AuthCard({ authForm, authUser, onChange, onLogin, onLogout, onRegister }) {
  if (authUser) {
    return (
      <section className="sidebarCard">
        <p className="cardEyebrow">Account</p>
        <h2>{authUser.username}</h2>
        <p className="cardMuted">Signed in. Session history will be stored on your account.</p>
        <button className="button secondary" onClick={onLogout}>Sign out</button>
      </section>
    );
  }

  return (
    <section className="sidebarCard">
      <p className="cardEyebrow">Account1</p>
      <h2>Sign in to keep sessions</h2>
      <div className="fieldStack">
        <input
          className="textInput"
          value={authForm.username}
          onChange={(event) => onChange("username", event.target.value)}
          placeholder="username"
        />
        <input
          className="textInput"
          type="password"
          value={authForm.password}
          onChange={(event) => onChange("password", event.target.value)}
          placeholder="password"
        />
      </div>
      <div className="buttonRow">
        <button className="button ghost" onClick={onRegister}>Registe111r</button>
        <button className="button secondary" onClick={onLogin}>Sign in</button>
      </div>
    </section>
  );
}

export default function WorkspaceSidebar({ workspace }) {
  const { activeSessionId, authForm, authUser, ingesting, sessions, status } = workspace;
  const { createSession, ingest, login, logout, openSession, register, updateAuthField } = workspace.actions;

  return (
    <aside className="sidebar">
      <div className="brandBlock">
        <p className="brandKicker">RAG Workspace</p>
        <h1>Chat Retrieval Desk</h1>
        <p className="brandText">A single workspace for sessions, ingestion, account state, and document-grounded replies.</p>
      </div>

      <AuthCard
        authForm={authForm}
        authUser={authUser}
        onChange={updateAuthField}
        onLogin={login}
        onLogout={logout}
        onRegister={register}
      />

      <section className="sidebarCard">
        <p className="cardEyebrow">Knowledge Base</p>
        <h2>Document ingestion</h2>
        <p className="cardMuted">Re-index the `data/` directory and refresh the vector store.</p>
        <button className="button primary" onClick={ingest} disabled={ingesting}>
          {ingesting ? "Indexing..." : "Rebuild knowledge base"}
        </button>
      </section>

      <section className="sidebarCard">
        <div className="cardHeader">
          <div>
            <p className="cardEyebrow">Sessions</p>
            <h2>Conversation history</h2>
          </div>
          {authUser ? (
            <button className="button ghost compact" onClick={createSession}>New</button>
          ) : null}
        </div>
        {authUser ? (
          sessions.length > 0 ? (
            <div className="sessionList">
              {sessions.map((session) => (
                <button
                  key={session.id}
                  className={`sessionItem ${session.id === activeSessionId ? "active" : ""}`}
                  onClick={() => openSession(session.id)}
                >
                  <span>{session.title}</span>
                  <small>#{session.id}</small>
                </button>
              ))}
            </div>
          ) : (
            <p className="emptyNote">No saved sessions yet. The first successful message will create one.</p>
          )
        ) : (
          <p className="emptyNote">Guest mode can chat immediately, but history is not persisted.</p>
        )}
      </section>

      <section className={`statusCard ${status.tone}`}>
        <p className="cardEyebrow">Status</p>
        <strong>{status.message}</strong>
      </section>
    </aside>
  );
}
