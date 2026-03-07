function AuthCard({ authForm, authUser, onChange, onLogin, onLogout, onRegister }) {
  if (authUser) {
    return (
      <section className="sidebarCard">
        <p className="cardEyebrow">Account</p>
        <h2>{authUser.username}</h2>
        <p className="cardMuted">Signed in. Session history will be stored on your account.</p>
        <p className="authHint">Ledger mode active</p>
        <button className="button secondary" onClick={onLogout}>Sign out</button>
      </section>
    );
  }

  return (
    <section className="sidebarCard">
      <p className="cardEyebrow">Account</p>
      <h2>Sign in to keep sessions</h2>
      <p className="cardMuted">Unlock a persistent conversation ledger and restore previous runs.</p>
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
        <button className="button ghost" onClick={onRegister}>Register</button>
        <button className="button secondary" onClick={onLogin}>Sign in</button>
      </div>
      <p className="authHint">Guest mode remains available</p>
    </section>
  );
}

export default function WorkspaceSidebar({ workspace }) {
  const { activeSessionId, authForm, authUser, ingesting, sessions, status } = workspace;
  const { createSession, ingest, login, logout, openSession, register, updateAuthField } = workspace.actions;

  return (
    <aside className="sidebar">
      <div className="brandBlock">
        <p className="brandKicker">Terminal Editorial / RAG</p>
        <h1>Retrieval Ledger</h1>
        <p className="brandText">A live research desk for indexed documents, persistent sessions, and grounded replies.</p>
        <div className="brandMetrics">
          <div>
            <p className="metricLabel">Mode</p>
            <strong>{authUser ? "Account" : "Guest"}</strong>
          </div>
          <div>
            <p className="metricLabel">Sessions</p>
            <strong>{authUser ? sessions.length : "--"}</strong>
          </div>
        </div>
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
        <h2>Recompile the archive</h2>
        <p className="cardMuted">Re-index the `data/` directory and refresh the retrieval corpus used by the assistant.</p>
        <button className="button primary" onClick={ingest} disabled={ingesting}>
          {ingesting ? "Indexing..." : "Run ingest pass"}
        </button>
      </section>

      <section className="sidebarCard">
        <div className="cardHeader">
          <div>
            <p className="cardEyebrow">Sessions</p>
            <h2>Conversation ledger</h2>
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
                  <span className="sessionIndex">Entry #{session.id}</span>
                  <span>{session.title}</span>
                  <small>#{session.id}</small>
                </button>
              ))}
            </div>
          ) : (
            <p className="emptyNote">No saved entries yet. The first successful message will create one.</p>
          )
        ) : (
          <p className="emptyNote">Guest mode can chat immediately, but the ledger is not persisted.</p>
        )}
      </section>

      <section className={`statusCard ${status.tone}`}>
        <p className="cardEyebrow">System status</p>
        <strong>{status.message}</strong>
      </section>
    </aside>
  );
}
