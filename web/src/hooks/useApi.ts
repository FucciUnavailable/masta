import { useCallback, useEffect, useState } from 'react'

export type Loadable<T> =
  | { status: 'loading' }
  | { status: 'error'; error: string }
  | { status: 'ready'; data: T }

export function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : String(err)
}

/**
 * Load data on mount, with a `reload` to refetch after a change. Reloading keeps showing
 * the current data until the new data arrives. Pass a stable function (e.g. `api.goals`),
 * not an inline arrow, or the request re-fires on every render.
 */
export function useResource<T>(load: () => Promise<T>): {
  state: Loadable<T>
  reload: () => void
} {
  const [state, setState] = useState<Loadable<T>>({ status: 'loading' })
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let live = true
    load().then(
      (data) => {
        if (live) setState({ status: 'ready', data })
      },
      (err: unknown) => {
        if (live) setState({ status: 'error', error: errorMessage(err) })
      },
    )
    return () => {
      live = false
    }
  }, [load, version])

  const reload = useCallback(() => setVersion((v) => v + 1), [])
  return { state, reload }
}

/** Load data once on mount. See `useResource` for the stable-function caveat. */
export function useApi<T>(load: () => Promise<T>): Loadable<T> {
  return useResource(load).state
}
