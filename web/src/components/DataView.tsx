import type { ReactNode } from 'react'
import type { Loadable } from '../hooks/useApi'

interface Props<T> {
  state: Loadable<T[]>
  empty: ReactNode
  children: (rows: T[]) => ReactNode
}

/** Renders the loading / error / empty states shared by every list page. */
export function DataView<T>({ state, empty, children }: Props<T>) {
  if (state.status === 'loading') return <p className="muted">Loading…</p>
  if (state.status === 'error') {
    return (
      <p className="notice notice--error" role="alert">
        {state.error}
      </p>
    )
  }
  if (state.data.length === 0) return <p className="muted">{empty}</p>
  return <>{children(state.data)}</>
}
