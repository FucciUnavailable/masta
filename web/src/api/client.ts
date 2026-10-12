import type {
  ChatEvent,
  ChatRequest,
  CheckIn,
  CheckInCreate,
  Coach,
  CoachCreate,
  CoachDetail,
  CoachUpdate,
  Goal,
  GoalCreate,
  GoalStatus,
  Health,
  Message,
  Profile,
  ProfileUpdate,
  Session,
  Settings,
} from './types'

// Same-origin: Vite proxies /api in dev, and `masta serve` hosts both in production.
const BASE = '/api'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function errorFrom(res: Response): Promise<ApiError> {
  let message = res.statusText || `Request failed (${res.status})`
  try {
    // FastAPI reports errors as { detail: string } or { detail: [{ msg }, ...] }.
    const { detail } = (await res.json()) as { detail?: unknown }
    if (typeof detail === 'string') {
      message = detail
    } else if (Array.isArray(detail)) {
      message = detail.map((d: { msg?: string }) => d.msg).join('; ')
    }
  } catch {
    // Not JSON (e.g. a proxy error page) — keep the status text.
  }
  return new ApiError(res.status, message)
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, init)
  if (!res.ok) throw await errorFrom(res)
  // Deletes answer 204 with no body; callers type those as `void`.
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

function withBody(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

function query(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) search.set(key, String(value))
  }
  const qs = search.toString()
  return qs ? `?${qs}` : ''
}

/** Stream one coaching turn as it is generated. Ends after a `done` or `error` event. */
async function* streamChat(
  body: ChatRequest,
  signal?: AbortSignal,
): AsyncGenerator<ChatEvent> {
  const res = await fetch(`${BASE}/chat`, { ...withBody('POST', body), signal })
  if (!res.ok) throw await errorFrom(res)
  if (!res.body) throw new ApiError(res.status, 'Empty response body')

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) return
    buffer += decoder.decode(value, { stream: true })

    // Server-sent events are separated by a blank line; a chunk may hold several or a part.
    let end: number
    while ((end = buffer.indexOf('\n\n')) !== -1) {
      const frame = buffer.slice(0, end)
      buffer = buffer.slice(end + 2)
      if (frame.startsWith('data: ')) {
        yield JSON.parse(frame.slice('data: '.length)) as ChatEvent
      }
    }
  }
}

export const api = {
  health: () => request<Health>('/health'),
  settings: () => request<Settings>('/settings'),
  setDefaultProfile: (name: string) =>
    request<Settings>(
      '/settings',
      withBody('PATCH', { default_profile: name }),
    ),

  profiles: () => request<Profile[]>('/profiles'),
  saveProfile: (name: string, profile: ProfileUpdate) =>
    request<Profile>(
      `/profiles/${encodeURIComponent(name)}`,
      withBody('PUT', profile),
    ),
  deleteProfile: (name: string) =>
    request<void>(`/profiles/${encodeURIComponent(name)}`, {
      method: 'DELETE',
    }),

  coaches: () => request<Coach[]>('/coaches'),
  coach: (name: string) =>
    request<CoachDetail>(`/coaches/${encodeURIComponent(name)}`),
  createCoach: (coach: CoachCreate) =>
    request<CoachDetail>('/coaches', withBody('POST', coach)),
  updateCoach: (name: string, coach: CoachUpdate) =>
    request<CoachDetail>(
      `/coaches/${encodeURIComponent(name)}`,
      withBody('PUT', coach),
    ),
  deleteCoach: (name: string) =>
    request<void>(`/coaches/${encodeURIComponent(name)}`, { method: 'DELETE' }),

  goals: (status?: GoalStatus) => request<Goal[]>(`/goals${query({ status })}`),
  createGoal: (goal: GoalCreate) =>
    request<Goal>('/goals', withBody('POST', goal)),
  setGoalStatus: (id: number, status: GoalStatus) =>
    request<Goal>(`/goals/${id}`, withBody('PATCH', { status })),

  checkins: (limit?: number) =>
    request<CheckIn[]>(`/checkins${query({ limit })}`),
  createCheckin: (checkin: CheckInCreate) =>
    request<CheckIn>('/checkins', withBody('POST', checkin)),

  sessions: () => request<Session[]>('/sessions'),
  createSession: (coach: string) =>
    request<Session>('/sessions', withBody('POST', { coach })),
  deleteSession: (id: number) =>
    request<void>(`/sessions/${id}`, { method: 'DELETE' }),
  sessionMessages: (id: number) =>
    request<Message[]>(`/sessions/${id}/messages`),

  messages: (coach?: string, limit?: number) =>
    request<Message[]>(`/messages${query({ coach, limit })}`),
  streamChat,
}
