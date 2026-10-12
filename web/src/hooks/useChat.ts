import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { Session } from '../api/types'
import { errorMessage } from './useApi'

export interface ChatMessage {
  key: number
  role: 'user' | 'assistant'
  content: string
}

interface Thread {
  messages: ChatMessage[]
  status: 'idle' | 'loading' | 'streaming'
  error: string | null
}

interface Callbacks {
  /** The first message of a new chat created its session. */
  onSessionStarted: (session: Session) => void
  /** A turn finished, failed, or was stopped. */
  onTurnEnd: () => void
}

/**
 * One chat thread: its messages, `send` to stream a coaching turn into it, and `stop` to cut
 * a reply short. Pass the session to resume, or `null` for a new chat, whose session is
 * created by the first `send`.
 *
 * The thread belongs to the component instance — mount a fresh one (change its `key`) to
 * show a different session.
 */
export function useChat(initialSessionId: number | null, callbacks: Callbacks) {
  const [thread, setThread] = useState<Thread>({
    messages: [],
    status: initialSessionId === null ? 'idle' : 'loading',
    error: null,
  })
  // Only the session this thread was mounted with is loaded; a new chat's id arrives later
  // as a prop, by which time its messages are already here.
  const [initial] = useState(initialSessionId)
  const sessionId = useRef(initial)
  const abort = useRef<AbortController | null>(null)
  const nextKey = useRef(0)
  const latest = useRef(callbacks)
  useEffect(() => {
    latest.current = callbacks
  })

  useEffect(() => {
    let live = true
    const loading = initial === null ? null : api.sessionMessages(initial)
    loading?.then(
      (rows) => {
        if (!live) return
        const messages = rows
          .filter((m) => m.role === 'user' || m.role === 'assistant')
          .map((m) => ({
            key: nextKey.current++,
            role: m.role as ChatMessage['role'],
            content: m.content,
          }))
        setThread({ messages, status: 'idle', error: null })
      },
      (err: unknown) => {
        if (live) {
          setThread({ messages: [], status: 'idle', error: errorMessage(err) })
        }
      },
    )
    return () => {
      live = false
      // Leaving ends the request; the server keeps what was streamed so far.
      abort.current?.abort()
    }
  }, [initial])

  const send = useCallback(
    async (coach: string, text: string, profile: string | null) => {
      const controller = new AbortController()
      abort.current = controller

      const replyKey = nextKey.current + 1
      const pending: ChatMessage[] = [
        { key: nextKey.current, role: 'user', content: text },
        { key: replyKey, role: 'assistant', content: '' },
      ]
      nextKey.current += 2
      setThread((t) => ({
        messages: [...t.messages, ...pending],
        status: 'streaming',
        error: null,
      }))

      try {
        if (sessionId.current === null) {
          const session = await api.createSession(coach)
          if (controller.signal.aborted) return
          sessionId.current = session.id
          latest.current.onSessionStarted(session)
        }
        const events = api.streamChat(
          { coach, message: text, session_id: sessionId.current, profile },
          controller.signal,
        )
        for await (const event of events) {
          if (event.type === 'error') throw new Error(event.message)
          if (event.type === 'delta') {
            setThread((t) => ({
              ...t,
              messages: t.messages.map((m) =>
                m.key === replyKey
                  ? { ...m, content: m.content + event.text }
                  : m,
              ),
            }))
          }
        }
      } catch (err) {
        // A stop is the user's choice, not a failure.
        if (!controller.signal.aborted) {
          setThread((t) => ({ ...t, error: errorMessage(err) }))
        }
      } finally {
        setThread((t) => ({
          ...t,
          status: 'idle',
          // Drop the reply placeholder if nothing arrived to fill it.
          messages: t.messages.filter(
            (m) => m.key !== replyKey || m.content !== '',
          ),
        }))
        latest.current.onTurnEnd()
      }
    },
    [],
  )

  const stop = useCallback(() => abort.current?.abort(), [])

  return { ...thread, send, stop }
}
