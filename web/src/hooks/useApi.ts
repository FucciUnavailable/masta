import { useEffect, useState } from 'react'

export type Loadable<T> =
  | { status: 'loading' }
  | { status: 'error'; error: string }
  | { status: 'ready'; data: T }

/**
 * Load data once on mount. Pass a stable function (e.g. `api.goals`), not an inline arrow,
 * or the request re-fires on every render.
 */
export function useApi<T>(load: () => Promise<T>): Loadable<T> {
  const [state, setState] = useState<Loadable<T>>({ status: 'loading' })

  useEffect(() => {
    let live = true
    load().then(
      (data) => {
        if (live) setState({ status: 'ready', data })
      },
      (err: unknown) => {
        const error = err instanceof Error ? err.message : String(err)
        if (live) setState({ status: 'error', error })
      },
    )
    return () => {
      live = false
    }
  }, [load])

  return state
}
