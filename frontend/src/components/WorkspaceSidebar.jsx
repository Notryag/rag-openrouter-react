import { useLocale } from "../hooks/useLocale.js";

function AuthCard({ authForm, authUser, onChange, onLogin, onLogout, onRegister }) {
  const { copy } = useLocale();
  const sidebarCopy = copy.sidebar;

  if (authUser) {
    return (
      <section className="sidebarCard">
        <p className="cardEyebrow">{sidebarCopy.accountEyebrow}</p>
        <h2>{authUser.username}</h2>
        <p className="cardMuted">{sidebarCopy.accountSignedIn}</p>
        <p className="authHint">{sidebarCopy.accountActive}</p>
        <button className="button secondary" onClick={onLogout}>{sidebarCopy.signOut}</button>
      </section>
    );
  }

  return (
    <section className="sidebarCard">
      <p className="cardEyebrow">{sidebarCopy.accountEyebrow}</p>
      <h2>{sidebarCopy.signInTitle}</h2>
      <p className="cardMuted">{sidebarCopy.signInDescription}</p>
      <div className="fieldStack">
        <input
          className="textInput"
          value={authForm.username}
          onChange={(event) => onChange("username", event.target.value)}
          placeholder={sidebarCopy.usernamePlaceholder}
        />
        <input
          className="textInput"
          type="password"
          value={authForm.password}
          onChange={(event) => onChange("password", event.target.value)}
          placeholder={sidebarCopy.passwordPlaceholder}
        />
      </div>
      <div className="buttonRow">
        <button className="button ghost" onClick={onRegister}>{sidebarCopy.register}</button>
        <button className="button secondary" onClick={onLogin}>{sidebarCopy.signIn}</button>
      </div>
      <p className="authHint">{sidebarCopy.guestAvailable}</p>
    </section>
  );
}

export default function WorkspaceSidebar({ workspace }) {
  const { activeSessionId, authForm, authUser, ingesting, sessions, status } = workspace;
  const { createSession, ingest, login, logout, openSession, register, updateAuthField } = workspace.actions;
  const { copy, locale, locales, setLocale } = useLocale();
  const sidebarCopy = copy.sidebar;
  const getSessionTitle = (title) => (title === "New chat" ? sidebarCopy.newChatTitle : title);

  return (
    <aside className="sidebar">
      <div className="brandBlock">
        <p className="brandKicker">{sidebarCopy.brandKicker}</p>
        <h1>{sidebarCopy.title}</h1>
        <p className="brandText">{sidebarCopy.description}</p>
        <div className="brandMetrics">
          <div>
            <p className="metricLabel">{sidebarCopy.mode}</p>
            <strong>{authUser ? sidebarCopy.accountMode : sidebarCopy.guestMode}</strong>
          </div>
          <div>
            <p className="metricLabel">{sidebarCopy.sessions}</p>
            <strong>{authUser ? sessions.length : "--"}</strong>
          </div>
        </div>
      </div>

      <section className="sidebarCard">
        <p className="cardEyebrow">{sidebarCopy.languageEyebrow}</p>
        <div className="cardHeader">
          <h2>{sidebarCopy.languageTitle}</h2>
          <div className="buttonRow">
            {locales.map((option) => (
              <button
                key={option.value}
                className={`button compact ${locale === option.value ? "secondary" : "ghost"}`}
                onClick={() => setLocale(option.value)}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      <AuthCard
        authForm={authForm}
        authUser={authUser}
        onChange={updateAuthField}
        onLogin={login}
        onLogout={logout}
        onRegister={register}
      />

      <section className="sidebarCard">
        <p className="cardEyebrow">{sidebarCopy.knowledgeEyebrow}</p>
        <h2>{sidebarCopy.knowledgeTitle}</h2>
        <p className="cardMuted">{sidebarCopy.knowledgeDescription}</p>
        <button className="button primary" onClick={ingest} disabled={ingesting}>
          {ingesting ? sidebarCopy.ingestLoading : sidebarCopy.ingest}
        </button>
      </section>

      <section className="sidebarCard">
        <div className="cardHeader">
          <div>
            <p className="cardEyebrow">{sidebarCopy.sessionEyebrow}</p>
            <h2>{sidebarCopy.sessionTitle}</h2>
          </div>
          {authUser ? (
            <button className="button ghost compact" onClick={createSession}>{sidebarCopy.new}</button>
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
                  <span className="sessionIndex">{sidebarCopy.sessionEntry(session.id)}</span>
                  <span>{getSessionTitle(session.title)}</span>
                  <small>#{session.id}</small>
                </button>
              ))}
            </div>
          ) : (
            <p className="emptyNote">{sidebarCopy.emptySaved}</p>
          )
        ) : (
          <p className="emptyNote">{sidebarCopy.emptyGuest}</p>
        )}
      </section>

      <section className={`statusCard ${status.tone}`}>
        <p className="cardEyebrow">{sidebarCopy.systemStatus}</p>
        <strong>{status.message}</strong>
      </section>
    </aside>
  );
}
