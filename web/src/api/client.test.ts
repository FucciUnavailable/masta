import { expect, test, vi } from 'vitest'
import { api, ApiError } from './client'
import type { ChatEvent } from './types'

function stubFetch(respond: () => Response) {
  const fetchMock = vi.fn(async () => respond())
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

/** A streaming response that delivers `chunks` one read at a time. */
function streamOf(chunks: string[]): Response {
  const encoder = new TextEncoder()
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk))
      controller.close()
    },
  })
  return new Response(body)
}

test('builds query strings and sends JSON bodies', async () => {
  const fetchMock = stubFetch(() => Response.json([]))
  await api.goals('active')
  expect(fetchMock).toHaveBeenLastCalledWith(
    '/api/goals?status=active',
    undefined,
  )

  await api.goals()
  expect(fetchMock).toHaveBeenLastCalledWith('/api/goals', undefined)

  await api.createGoal({ title: 'Learn X' })
  expect(fetchMock).toHaveBeenLastCalledWith(
    '/api/goals',
    expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ title: 'Learn X' }),
    }),
  )
})

test('surfaces FastAPI error details', async () => {
  stubFetch(() =>
    Response.json({ detail: "Unknown coach 'x'." }, { status: 404 }),
  )
  const error = await api.coach('x').catch((e: unknown) => e)
  expect(error).toBeInstanceOf(ApiError)
  expect(error).toMatchObject({ status: 404, message: "Unknown coach 'x'." })

  stubFetch(() =>
    Response.json(
      { detail: [{ msg: 'too short' }, { msg: 'bad status' }] },
      { status: 422 },
    ),
  )
  await expect(api.createGoal({ title: '' })).rejects.toThrow(
    'too short; bad status',
  )
})

test('streamChat reassembles events split across network chunks', async () => {
  stubFetch(() =>
    streamOf([
      'data: {"type": "delta", "text": "Hel',
      'lo "}\n\ndata: {"type": "delta", "text": "there"}\n',
      '\ndata: {"type": "done"}\n\n',
    ]),
  )

  const events: ChatEvent[] = []
  for await (const event of api.streamChat({ coach: 'c', message: 'hi' })) {
    events.push(event)
  }
  expect(events).toEqual([
    { type: 'delta', text: 'Hello ' },
    { type: 'delta', text: 'there' },
    { type: 'done' },
  ])
})

test('streamChat rejects on an HTTP error before streaming', async () => {
  stubFetch(() => Response.json({ detail: 'Unknown coach' }, { status: 404 }))
  const stream = api.streamChat({ coach: 'nope', message: 'hi' })
  await expect(stream.next()).rejects.toThrow('Unknown coach')
})
