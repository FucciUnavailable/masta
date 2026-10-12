import { useEffect, useRef, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import Markdown from 'react-markdown'
import { Link, useSearchParams } from 'react-router'
import { api } from '../api/client'
import type { Coach, Profile, Session } from '../api/types'
import { DataView } from '../components/DataView'
import { useAction } from '../hooks/useAction'
import { useApi, useResource } from '../hooks/useApi'
import { useChat } from '../hooks/useChat'
import type { ChatMessage } from '../hooks/useChat'

function coachLabel(coaches: Coach[], name: string): string {
  return coaches.find((c) => c.name === name)?.display_name ?? name
}

interface SessionListProps {
  sessions: Session[]
  coaches: Coach[]
  activeId: number | null
  onDelete: (session: Session) => void
}

function SessionList({
  sessions,
  coaches,
  activeId,
  onDelete,
}: SessionListProps) {
  return (
    <ul className="session-list">
      {sessions.map((session) => (
        <li
          key={session.id}
          className={session.id === activeId ? 'session active' : 'session'}
        >
          <Link to={`/?session=${session.id}`} className="session-link">
            <span className="session-title">{session.title || 'New chat'}</span>
            <span className="session-meta">
              {coachLabel(coaches, session.coach)} ·{' '}
              {new Date(session.updated_at).toLocaleDateString()}
            </span>
          </Link>
          <button
            type="button"
            className="icon-button"
            aria-label={`Delete “${session.title || 'New chat'}”`}
            onClick={() => onDelete(session)}
          >
            ×
          </button>
        </li>
      ))}
    </ul>
  )
}

function Bubble({
  message,
  streaming,
}: {
  message: ChatMessage
  streaming: boolean
}) {
  if (message.role === 'user') {
    return <li className="bubble bubble--user">{message.content}</li>
  }
  return (
    <li className="bubble bubble--coach">
      {message.content ? (
        <Markdown>{message.content}</Markdown>
      ) : (
        streaming && <span className="muted">Thinking…</span>
      )}
    </li>
  )
}

/** Why the profile a turn would use can't answer yet, if it can't. */
function profileProblem(profile: Profile | undefined): string | null {
  if (!profile || profile.configured) return null
  if (profile.missing_env.length > 0) {
    return `The “${profile.name}” model needs ${profile.missing_env.join(', ')} set where masta serve runs.`
  }
  return `masta can’t tell whether the “${profile.name}” model (${profile.provider}) is set up.`
}

interface ThreadProps {
  sessionId: number | null
  /** The coach to talk to; null when the session's coach isn't known (yet). */
  coachName: string | null
  profileName: string
  problem: string | null
  onSessionStarted: (session: Session) => void
  onTurnEnd: () => void
}

/** The message log and composer for one chat. Keyed by the parent, one instance per chat. */
function ChatThread({
  sessionId,
  coachName,
  profileName,
  problem,
  onSessionStarted,
  onTurnEnd,
}: ThreadProps) {
  const chat = useChat(sessionId, { onSessionStarted, onTurnEnd })
  const [draft, setDraft] = useState('')

  // Follow the reply as it streams. The log scrolls on wide screens, the page on narrow.
  const end = useRef<HTMLLIElement>(null)
  useEffect(() => {
    end.current?.scrollIntoView?.({ block: 'end' })
  }, [chat.messages])

  const streaming = chat.status === 'streaming'
  const canSend =
    coachName !== null && draft.trim() !== '' && chat.status === 'idle'

  function submit(event?: FormEvent) {
    event?.preventDefault()
    if (!canSend) return
    void chat.send(coachName, draft.trim(), profileName || null)
    setDraft('')
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <>
      <ol className="chat-log" aria-live="polite">
        {chat.status === 'loading' && <li className="muted">Loading…</li>}
        {chat.status === 'idle' &&
          chat.messages.length === 0 &&
          !chat.error && (
            <li className="muted">
              Say what you’re working toward, or where you’re stuck.
            </li>
          )}
        {chat.messages.map((message) => (
          <Bubble key={message.key} message={message} streaming={streaming} />
        ))}
        <li ref={end} className="chat-end" aria-hidden="true" />
      </ol>

      {chat.error && (
        <p className="notice notice--error" role="alert">
          {chat.error}
        </p>
      )}
      {problem && (
        <p className="notice">
          {problem} See <Link to="/settings">Settings</Link>.
        </p>
      )}

      <form className="composer" onSubmit={submit}>
        <textarea
          aria-label="Message"
          placeholder="Message your coach…"
          rows={2}
          value={draft}
          disabled={coachName === null}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
        />
        {streaming ? (
          <button type="button" className="button" onClick={chat.stop}>
            Stop
          </button>
        ) : (
          <button
            type="submit"
            className="button button--primary"
            disabled={!canSend}
          >
            Send
          </button>
        )}
      </form>
    </>
  )
}

export function ChatPage() {
  const [params, setParams] = useSearchParams()
  const sessionParam = Number(params.get('session'))
  const sessionId =
    Number.isInteger(sessionParam) && sessionParam > 0 ? sessionParam : null

  const coaches = useApi(api.coaches)
  const profiles = useApi(api.profiles)
  const { state: sessions, reload: reloadSessions } = useResource(api.sessions)
  const deletion = useAction()
  const [profileName, setProfileName] = useState('')

  // A new chat becomes a session on its first message, and the URL follows. `started` is
  // that session, so the thread keeps its key (stays mounted, keeps streaming) across the
  // move. Leaving it ends that: the next new chat gets a fresh thread.
  const [chatNo, setChatNo] = useState(0)
  const [started, setStarted] = useState<Session | null>(null)
  const [seenSessionId, setSeenSessionId] = useState(sessionId)
  if (seenSessionId !== sessionId) {
    setSeenSessionId(sessionId)
    if (started && seenSessionId === started.id) {
      setStarted(null)
      setChatNo(chatNo + 1)
    }
  }
  const threadKey =
    sessionId === null || sessionId === started?.id
      ? `new-${chatNo}`
      : `session-${sessionId}`

  function onSessionStarted(session: Session) {
    setStarted(session)
    setParams({ session: String(session.id) })
  }

  const coachRows = coaches.status === 'ready' ? coaches.data : []
  const sessionRows = sessions.status === 'ready' ? sessions.data : []
  const session =
    sessionRows.find((s) => s.id === sessionId) ??
    (started?.id === sessionId ? started : null)
  const coachName =
    session?.coach ?? (sessionId === null ? params.get('coach') : null)
  const coach = coachRows.find((c) => c.name === coachName)

  const profileRows = profiles.status === 'ready' ? profiles.data : []
  const usedProfile =
    profileRows.find((p) => p.name === (profileName || coach?.model_profile)) ??
    profileRows.find((p) => p.is_default)

  async function deleteSession(target: Session) {
    if (!window.confirm(`Delete “${target.title || 'New chat'}”?`)) return
    const deleted = await deletion.run(() => api.deleteSession(target.id))
    if (deleted && target.id === sessionId) setParams({})
    reloadSessions()
  }

  return (
    <div className="chat">
      <aside className="chat-sessions" aria-label="Sessions">
        <Link to="/" className="button">
          New chat
        </Link>
        {deletion.error && (
          <p className="notice notice--error" role="alert">
            {deletion.error}
          </p>
        )}
        <DataView state={sessions} empty="No sessions yet.">
          {(rows) => (
            <SessionList
              sessions={rows}
              coaches={coachRows}
              activeId={sessionId}
              onDelete={deleteSession}
            />
          )}
        </DataView>
      </aside>

      <section className="chat-main">
        <header className="page-header chat-header">
          <div>
            <h1>{coach?.display_name ?? coachName ?? 'Chat'}</h1>
            <p>
              {coachName || sessionId
                ? session?.title || 'New chat'
                : 'Pick a coach to start a session.'}
            </p>
          </div>
          {coachName && profileRows.length > 0 && (
            <label className="field field--inline">
              <span>Model</span>
              <select
                value={profileName}
                onChange={(e) => setProfileName(e.target.value)}
              >
                <option value="">
                  Coach default
                  {coach?.model_profile ? ` (${coach.model_profile})` : ''}
                </option>
                {profileRows.map((p) => (
                  <option key={p.name} value={p.name}>
                    {p.name}
                    {p.configured ? '' : ' (not set up)'}
                  </option>
                ))}
              </select>
            </label>
          )}
        </header>

        {!coachName && !sessionId ? (
          <DataView state={coaches} empty="No coaches found.">
            {(rows) => (
              <ul className="cards">
                {rows.map((c) => (
                  <li key={c.name} className="card">
                    <h2>
                      <Link to={`/?coach=${encodeURIComponent(c.name)}`}>
                        {c.display_name}
                      </Link>
                    </h2>
                    <p>{c.description}</p>
                    <p className="tags">
                      {c.tags.map((tag) => (
                        <span key={tag} className="tag">
                          {tag}
                        </span>
                      ))}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </DataView>
        ) : (
          <ChatThread
            key={threadKey}
            sessionId={sessionId}
            coachName={coachName}
            profileName={profileName}
            problem={coachName ? profileProblem(usedProfile) : null}
            onSessionStarted={onSessionStarted}
            onTurnEnd={reloadSessions}
          />
        )}
      </section>
    </div>
  )
}
