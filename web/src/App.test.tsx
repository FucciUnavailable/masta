import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { expect, test, vi } from 'vitest'
import { AppRoutes } from './App'

type Handler = (body: unknown) => unknown

/**
 * Stub `fetch` per route. Keys are a path (`/api/goals`, meaning GET) or a method and path
 * (`POST /api/goals`); values are canned JSON, or a function of the request body returning
 * JSON or a `Response`. Anything unlisted is a 500. Returns the calls made, in order.
 */
function stubApi(routes: Record<string, unknown>) {
  const calls: { route: string; body: unknown }[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, init?: RequestInit) => {
      const method = init?.method ?? 'GET'
      const route = method === 'GET' ? url : `${method} ${url}`
      const body = init?.body ? JSON.parse(init.body as string) : undefined
      calls.push({ route, body })
      if (!(route in routes)) {
        return Response.json({ detail: `boom: ${route}` }, { status: 500 })
      }
      const value = routes[route]
      const result =
        typeof value === 'function' ? (value as Handler)(body) : value
      if (result instanceof Response) return result
      return result === undefined
        ? new Response(null, { status: 204 })
        : Response.json(result)
    }),
  )
  return calls
}

function sse(...events: object[]): Response {
  return new Response(
    events.map((e) => `data: ${JSON.stringify(e)}\n\n`).join(''),
  )
}

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <AppRoutes />
    </MemoryRouter>,
  )
}

const health = { status: 'ok', version: '0.1.0' }

const coach = {
  name: 'backend-engineering',
  display_name: 'Backend Engineering',
  description: 'Systems and APIs.',
  tags: ['software'],
  model_profile: null,
  tools: ['web_search'],
  editable: false,
}

const profile = {
  name: 'claude',
  model: 'anthropic/claude-sonnet-4-6',
  provider: 'anthropic',
  temperature: 0.7,
  max_tokens: null,
  api_base: null,
  configured: true,
  missing_env: [],
  is_default: true,
  builtin: true,
  customized: false,
}

const session = {
  id: 7,
  coach: 'backend-engineering',
  title: 'Learning Postgres',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-02T00:00:00Z',
}

function message(id: number, role: string, content: string) {
  return {
    id,
    coach: session.coach,
    session_id: 7,
    role,
    content,
    created_at: session.created_at,
  }
}

test('chat home lists coaches and past sessions inside the shell', async () => {
  stubApi({
    '/api/health': health,
    '/api/coaches': [coach],
    '/api/profiles': [profile],
    '/api/sessions': [session],
  })
  renderAt('/')

  expect(screen.getByRole('link', { name: 'Chat' })).toHaveClass('active')
  expect(
    await screen.findByRole('link', { name: 'Backend Engineering' }),
  ).toHaveAttribute('href', '/?coach=backend-engineering')
  expect(await screen.findByText('Learning Postgres')).toBeInTheDocument()
  expect(await screen.findByText('API v0.1.0')).toBeInTheDocument()
})

test('a first message starts a session and streams the reply', async () => {
  const calls = stubApi({
    '/api/coaches': [coach],
    '/api/profiles': [profile],
    '/api/sessions': [],
    'POST /api/sessions': { ...session, title: '' },
    'POST /api/chat': () =>
      sse(
        { type: 'delta', text: 'Start with ' },
        { type: 'delta', text: '**indexes**.' },
        { type: 'done' },
      ),
  })
  renderAt('/?coach=backend-engineering')

  const input = await screen.findByLabelText('Message')
  await waitFor(() => expect(input).toBeEnabled())
  fireEvent.change(input, { target: { value: 'How do I learn Postgres?' } })
  fireEvent.click(screen.getByRole('button', { name: 'Send' }))

  expect(
    await screen.findByText('How do I learn Postgres?'),
  ).toBeInTheDocument()
  // The reply is rendered as Markdown, and survives the move to the session's URL.
  expect(await screen.findByText('indexes')).toHaveProperty('tagName', 'STRONG')
  expect(input).toHaveValue('')

  expect(calls.find((c) => c.route === 'POST /api/chat')?.body).toEqual({
    coach: 'backend-engineering',
    message: 'How do I learn Postgres?',
    session_id: 7,
    profile: null,
  })
  // The thread it just streamed is not refetched and replaced.
  expect(calls.map((c) => c.route)).not.toContain('/api/sessions/7/messages')
})

test('an existing session loads its messages and reports stream errors', async () => {
  stubApi({
    '/api/coaches': [coach],
    '/api/profiles': [
      { ...profile, configured: false, missing_env: ['ANTHROPIC_API_KEY'] },
    ],
    '/api/sessions': [session],
    '/api/sessions/7/messages': [
      message(1, 'user', 'earlier question'),
      message(2, 'assistant', 'earlier answer'),
    ],
    'POST /api/chat': () =>
      sse(
        { type: 'delta', text: 'partial' },
        { type: 'error', message: 'no API key' },
      ),
  })
  renderAt('/?session=7')

  expect(await screen.findByText('earlier answer')).toBeInTheDocument()
  expect(await screen.findByText(/needs ANTHROPIC_API_KEY/)).toBeInTheDocument()

  const input = screen.getByLabelText('Message')
  await waitFor(() => expect(input).toBeEnabled())
  fireEvent.change(input, { target: { value: 'again' } })
  fireEvent.keyDown(input, { key: 'Enter' })

  expect(await screen.findByText('no API key')).toBeInTheDocument()
  expect(screen.getByText('partial')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Send' })).toBeInTheDocument()
})

test('deleting the open session returns to the coach picker', async () => {
  vi.stubGlobal('confirm', () => true)
  const calls = stubApi({
    '/api/coaches': [coach],
    '/api/sessions': [session],
    '/api/sessions/7/messages': [],
    'DELETE /api/sessions/7': undefined,
  })
  renderAt('/?session=7')

  fireEvent.click(await screen.findByRole('button', { name: /Delete/ }))

  expect(
    await screen.findByText('Pick a coach to start a session.'),
  ).toBeInTheDocument()
  expect(calls.map((c) => c.route)).toContain('DELETE /api/sessions/7')
})

test('goals page shows goals with their status', async () => {
  stubApi({
    '/api/health': health,
    '/api/goals': [
      {
        id: 1,
        title: 'Learn Postgres',
        description: '',
        coach: null,
        status: 'paused',
        created_at: '2026-01-01T00:00:00',
        target_date: null,
      },
    ],
  })
  renderAt('/goals')

  expect(await screen.findByText('Learn Postgres')).toBeInTheDocument()
  expect(screen.getByText('paused')).toBeInTheDocument()
})

test('empty and failing requests render their own states', async () => {
  stubApi({ '/api/checkins': [] })
  renderAt('/check-ins')

  expect(await screen.findByText(/No check-ins yet/)).toBeInTheDocument()
  expect(await screen.findByText(/API unreachable/)).toBeInTheDocument()
})

test('unknown routes fall through to not-found', () => {
  stubApi({})
  renderAt('/nope')

  expect(screen.getByRole('heading', { name: 'Not found' })).toBeInTheDocument()
})
