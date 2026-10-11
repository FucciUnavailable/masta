import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { expect, test, vi } from 'vitest'
import { AppRoutes } from './App'

/** Stub `fetch` with canned JSON per API path; anything unlisted is a 500. */
function stubApi(routes: Record<string, unknown>) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) =>
      url in routes
        ? Response.json(routes[url])
        : Response.json({ detail: 'boom' }, { status: 500 }),
    ),
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

test('chat page lists coaches inside the shell', async () => {
  stubApi({
    '/api/health': health,
    '/api/coaches': [
      {
        name: 'backend-engineering',
        display_name: 'Backend Engineering',
        description: 'Systems and APIs.',
        tags: ['software'],
        model_profile: null,
        tools: [],
      },
    ],
  })
  renderAt('/')

  expect(screen.getByRole('link', { name: 'Chat' })).toHaveClass('active')
  expect(await screen.findByText('Backend Engineering')).toBeInTheDocument()
  expect(await screen.findByText('API v0.1.0')).toBeInTheDocument()
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
